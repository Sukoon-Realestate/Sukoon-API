"""Mobile rating API. Private and public projections both prohibit stale HTTP caches."""

from datetime import timedelta
from uuid import UUID
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.throttling import (
    SimpleRateThrottle,
    UserRateThrottle,
    AnonRateThrottle,
)
from core_apps.common.pagination import StandardResultsSetPagination
from core_apps.properties.models import PropertyVisit
from .models import (
    Lease,
    ReviewCase,
    ReviewOpportunity,
    ReviewDraft,
    ReviewReport,
    ReviewAppeal,
    ReputationAccessGrant,
    RentalOperationalCase,
)
from .renderers import FeatureJsonRenderer
from .services.reputation import generation, submission, visibility, moderation, grants
from .services.reputation.policy import (
    POLICY,
    CRITERIA,
    REPORT_REASONS,
    ReviewError,
    keys,
    revision,
    text_value,
    require_enabled,
)


class ReviewThrottle(SimpleRateThrottle):
    scope = "rating_context"
    rate = "120/hour"

    def get_cache_key(self, request, view):
        if (
            request.method in {"GET", "HEAD", "OPTIONS"}
            or not request.user.is_authenticated
        ):
            return None
        return f"rating:{request.user.pk}:{view.__class__.__name__}:{view.kwargs.get('identity', '')}"


class ReviewView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    throttle_classes = [ReviewThrottle, UserRateThrottle, AnonRateThrottle]

    def page(self, request, items, mapper=lambda x: x):
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(items, request, view=self)
        return paginator.get_paginated_response([mapper(i) for i in page])


def identity(value):
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        raise ReviewError("invalid_review_target", 400)


class ReviewCapabilitiesView(ReviewView):
    def get(self, request):
        enabled = getattr(settings, "REVIEWS_ENABLED", False)
        return Response(
            {
                "policy_version": POLICY["version"],
                "criteria_schema_version": POLICY["schema_version"],
                "generated_at": timezone.now().isoformat(),
                "enabled": enabled,
                "capabilities": {
                    "review_viewings": enabled,
                    "review_tenancies": enabled,
                    "review_housemates": enabled,
                    "share_reputation_summary": enabled,
                    "review_company_relationships": enabled,
                    "review_portfolio_rollups": enabled,
                },
                "blocking_reason_codes": [] if enabled else ["capability_unavailable"],
                "report_reasons": REPORT_REASONS,
            }
        )


class ReviewOpportunitiesView(ReviewView):
    def get(self, request):
        # Explicit source filters are authenticated source lookups, never client targets.
        lease_id, visit_id = request.query_params.get(
            "lease_id"
        ), request.query_params.get("visit_id")
        company_id = request.query_params.get("company_id")
        if lease_id:
            lease = get_object_or_404(
                Lease.objects.filter(Q(owner=request.user) | Q(tenant=request.user)),
                id=identity(lease_id),
            )
            if getattr(settings, "REVIEWS_ENABLED", False):
                generation.generate_tenancy(lease)
        if visit_id:
            visit = get_object_or_404(
                PropertyVisit, id=identity(visit_id), tenant=request.user
            )
            if getattr(settings, "REVIEWS_ENABLED", False):
                generation.generate_viewing(visit)
        query = (
            ReviewOpportunity.objects.filter(reviewer=request.user)
            .select_related("case")
            .order_by("-created_at", "id")
        )
        if company_id:
            from .services.reputation.company_authority import (
                accessible_company_opportunities,
            )

            query = (
                accessible_company_opportunities(request.user, identity(company_id))
                .select_related("case", "reviewer_company")
                .order_by("-created_at", "id")
            )
        if lease_id:
            query = query.filter(case__lease__tenancy_root_id=lease.tenancy_root_id)
        if visit_id:
            query = query.filter(case__visit__id=visit_id)
        return self.page(
            request,
            query,
            lambda item: visibility.opportunity_payload(item, request.user),
        )


class ReviewOpportunityView(ReviewView):
    def get(self, request, identity):
        return Response(
            visibility.opportunity_payload(
                submission.opportunity_for(request.user, identity), request.user
            )
        )

    def patch(self, request, identity):
        item = submission.opportunity_for(request.user, identity)

        def action():
            keys(
                request.data,
                ["request_key", "expected_revision", "reminders_enabled"],
                ["request_key", "expected_revision", "reminders_enabled"],
            )
            locked = ReviewOpportunity.objects.select_for_update().get(pk=item.pk)
            if locked.reviewer_company_id:
                from .services.reputation.company_authority import require_opportunity

                require_opportunity(request.user, locked, submit=True, lock=True)
            revision(locked, request.data["expected_revision"])
            if type(request.data["reminders_enabled"]) is not bool:
                raise ReviewError("invalid_review_target", 400)
            locked.reminders_enabled = request.data["reminders_enabled"]
            locked.save()
            return visibility.opportunity_payload(locked, request.user)

        return Response(
            submission.command(
                request.user,
                f"review.reminders.{identity}",
                request.data,
                action,
                item.id,
            )
        )


class ReviewSubmitView(ReviewView):
    def post(self, request, identity):
        return Response(
            submission.submit(request.user, identity, request.data), status=201
        )


class ReviewOperationView(ReviewView):
    def get(self, request, request_key):
        return Response(submission.lookup(request.user, request_key))


class ReviewDraftView(ReviewView):
    def get(self, request, identity):
        item = submission.opportunity_for(request.user, identity)
        draft = ReviewDraft.objects.filter(opportunity=item).first()
        if draft and timezone.now() >= item.case.closes_at + timedelta(days=7):
            draft.delete()
            draft = None
        return Response(
            {
                "revision": draft.revision if draft else 0,
                "payload": draft.payload if draft else None,
            }
        )

    def put(self, request, identity):
        item = submission.opportunity_for(request.user, identity)

        def action():
            locked = ReviewOpportunity.objects.select_for_update().get(pk=item.pk)
            if locked.reviewer_company_id:
                from .services.reputation.company_authority import require_opportunity

                require_opportunity(request.user, locked, submit=True, lock=True)
            keys(
                request.data,
                ["request_key", "expected_revision", "payload"],
                ["request_key", "expected_revision", "payload"],
            )
            if locked.state != "open" or timezone.now() >= locked.case.closes_at:
                raise ReviewError("review_window_closed")
            # Drafts are never accepted submissions and may contain incomplete scores.
            payload = request.data["payload"]
            import json

            if (
                not isinstance(payload, dict)
                or len(json.dumps(payload, ensure_ascii=False)) > 14000
            ):
                raise ReviewError("invalid_review_target", 400)
            draft = ReviewDraft.objects.filter(opportunity=locked).first()
            expected = request.data["expected_revision"]
            if type(expected) is not int or expected != (
                draft.revision if draft else 0
            ):
                raise ReviewError("revision_conflict")
            if draft:
                draft.payload, draft.updated_by, draft.revision = (
                    payload,
                    request.user,
                    draft.revision + 1,
                )
                draft.save()
            else:
                draft = ReviewDraft.objects.create(
                    opportunity=locked, updated_by=request.user, payload=payload
                )
            return {"revision": draft.revision, "payload": draft.payload}

        return Response(
            submission.command(
                request.user, f"review.draft.{identity}", request.data, action, item.id
            )
        )

    def delete(self, request, identity):
        item = submission.opportunity_for(request.user, identity)

        def action():
            locked = ReviewOpportunity.objects.select_for_update().get(pk=item.pk)
            if locked.reviewer_company_id:
                from .services.reputation.company_authority import require_opportunity

                require_opportunity(request.user, locked, submit=True, lock=True)
            draft = ReviewDraft.objects.filter(opportunity=locked).first()
            if draft:
                revision(draft, request.data.get("expected_revision"))
                draft.delete()
            return {"revision": 0, "payload": None}

        return Response(
            submission.command(
                request.user,
                f"review.draft_delete.{identity}",
                request.data,
                action,
                item.id,
            )
        )


class ReviewCollectionView(ReviewView):
    def get(self, request, collection):
        rows = visibility.sections()
        company_id = request.query_params.get("company_id")
        if company_id:
            from .services.reputation.company_authority import (
                accessible_company_opportunities,
                company_history,
            )

            company_id = identity(company_id)
            if collection == "mine":
                rows = rows.filter(
                    submission__opportunity__in=accessible_company_opportunities(
                        request.user, company_id
                    )
                )
            else:
                if not company_history(request.user, company_id):
                    raise NotFound()
                rows = rows.filter(subject_id=company_id)
        elif collection == "mine":
            rows = rows.filter(submission__opportunity__reviewer=request.user)
        else:
            rows = rows.filter(
                Q(subject_id=request.user.id)
                | Q(
                    subject_kind__startswith="property_",
                    submission__opportunity__case__party_b=request.user,
                )
            )
        rows = [
            s
            for s in rows.order_by("-created_at", "-id")
            if collection == "mine"
            or (
                visibility.visible(s, request.user)
                or visibility.participant_metadata(s, request.user)
            )
        ]
        return self.page(
            request, rows, lambda s: visibility.section_payload(s, request.user)
        )


class ReviewSubjectView(ReviewView):
    permission_classes = [AllowAny]

    def get(self, request, kind, identity, aggregate=False):
        if kind not in CRITERIA:
            raise NotFound()
        if aggregate:
            return Response(visibility.summary(kind, identity, request.user))
        rows = visibility.subject_rows(kind, identity, request.user)
        score = request.query_params.get("rating")
        if score:
            if score not in {"1", "2", "3", "4", "5"}:
                raise ReviewError("unsupported_criteria", 400)
            rows = [s for s in rows if s.overall_score == int(score)]
        return self.page(
            request,
            rows,
            lambda s: visibility.section_payload(
                s,
                request.user,
                public_only=kind
                in {
                    "property_visit",
                    "property_stay",
                    "person_landlord",
                    "organization_landlord",
                },
            ),
        )


class ReviewDetailView(ReviewView):
    permission_classes = [AllowAny]

    def get(self, request, identity):
        return Response(
            visibility.section_payload(
                visibility.section_for(request.user, identity), request.user
            )
        )


class ReviewActionView(ReviewView):
    def post(self, request, identity, action):
        return Response(
            moderation.section_action(request.user, identity, action, request.data)
        )


class ReviewReplyWithdrawView(ReviewView):
    def post(self, request, identity):
        return Response(moderation.withdraw_reply(request.user, identity, request.data))


class ReviewAppealView(ReviewView):
    def post(self, request, identity):
        return Response(
            moderation.appeal_decision(request.user, identity, request.data)
        )


class ReviewCaseView(ReviewView):
    def get(self, request, identity):
        item = (
            ReviewReport.objects.filter(id=identity, reporter=request.user).first()
            or ReviewAppeal.objects.filter(id=identity, appellant=request.user).first()
            or RentalOperationalCase.objects.filter(
                id=identity, opened_by=request.user, kind="review_eligibility"
            ).first()
        )
        if not item:
            raise NotFound()
        return Response(
            {
                "id": str(item.id),
                "state": getattr(item, "state", getattr(item, "status", "")),
                "revision": item.revision,
                "resolution": getattr(item, "resolution", ""),
            }
        )


class ReviewEligibilityRequestView(ReviewView):
    def post(self, request):
        keys(
            request.data,
            ["request_key", "source_kind", "source_id", "detail"],
            ["request_key", "source_kind", "source_id"],
        )
        kind = request.data["source_kind"]
        source_id = identity(request.data["source_id"])
        if kind == "viewing":
            source = get_object_or_404(PropertyVisit, id=source_id, tenant=request.user)
        elif kind == "tenancy":
            source = get_object_or_404(
                Lease.objects.filter(Q(owner=request.user) | Q(tenant=request.user)),
                id=source_id,
            )
        else:
            raise NotFound()

        def action():
            item, _ = RentalOperationalCase.objects.get_or_create(
                source_key=f"review-eligibility:{kind}:{source.id}:{request.user.id}",
                defaults={
                    "kind": "review_eligibility",
                    "opened_by": request.user,
                    "property": source.property,
                    "lease": source if kind == "tenancy" else None,
                    "team": "review_eligibility",
                    "next_action": "Inspect canonical attendance/occupancy evidence; never infer consent.",
                    "due_at": timezone.now() + timedelta(hours=72),
                    "reason": text_value(request.data.get("detail", ""), 1500),
                    "baseline": {"source_kind": kind, "source_id": str(source.id)},
                },
            )
            return {"id": str(item.id), "state": item.status, "revision": item.revision}

        return Response(
            submission.command(
                request.user,
                f"review.eligibility.{source.id}",
                request.data,
                action,
                source.id,
            )
        )


class ReputationGrantsView(ReviewView):
    def get(self, request):
        return self.page(
            request,
            ReputationAccessGrant.objects.filter(
                Q(owner=request.user) | Q(recipient=request.user)
            )
            .select_related("owner", "recipient")
            .order_by("-created_at"),
            lambda item: {
                **grants.payload(item),
                "can_revoke": item.owner_id == request.user.pk,
                "can_read": item.recipient_id == request.user.pk,
                "recipient_name": item.recipient.get_full_name,
                "owner_name": item.owner.get_full_name,
            },
        )

    def post(self, request):
        data = dict(request.data)
        if "recipient_id" in data:
            data["recipient_id"] = str(identity(data["recipient_id"]))
        return Response(grants.create(request.user, data), status=201)


class ReputationGrantView(ReviewView):
    def get(self, request, identity):
        return Response(grants.read(request.user, identity))

    def post(self, request, identity):
        return Response(grants.revoke(request.user, identity, request.data))


class ReviewModerationQueueView(ReviewView):
    def get(self, request):
        if not request.user.has_perm("features.moderate_reviews"):
            raise PermissionDenied()
        reason = text_value(request.query_params.get("reason", ""), 1000)
        if not reason:
            raise ReviewError("invalid_review_text", 400)
        rows = (
            visibility.sections()
            .filter(
                Q(content_state__in=["pending", "held"])
                | Q(reply__content_state__in=["pending", "held"])
            )
            .distinct()
            .order_by("created_at")
        )

        def project(item):
            moderation.require_moderator(request.user, item)
            submission.audit(item, request.user, "moderation_read", reason)
            return {
                "id": str(item.id),
                "original_comment": item.original_comment,
                "overall_score": item.overall_score,
                "state": item.content_state,
                "revision": item.revision,
                "reply": (
                    {
                        "id": str(item.reply.id),
                        "original_comment": item.reply.original_comment,
                        "state": item.reply.content_state,
                        "revision": item.reply.revision,
                    }
                    if hasattr(item, "reply")
                    else None
                ),
            }

        return self.page(request, rows, project)


class ReviewModerateView(ReviewView):
    def post(self, request, identity):
        return Response(moderation.moderate(request.user, identity, request.data))


class ReviewResolveAppealView(ReviewView):
    def post(self, request, identity):
        return Response(moderation.resolve_appeal(request.user, identity, request.data))


class ReputationRecipientsView(ReviewView):
    def get(self, request):
        from django.contrib.auth import get_user_model
        from django.db.models import Subquery

        leases = Lease.objects.filter(Q(owner=request.user) | Q(tenant=request.user))
        visits = PropertyVisit.objects.filter(tenant=request.user)
        query = (
            get_user_model()
            .objects.filter(
                Q(pk__in=Subquery(leases.values("owner_id")))
                | Q(pk__in=Subquery(visits.values("property__owner_id")))
                | Q(pk__in=Subquery(leases.values("tenant_id"))),
                is_active=True,
            )
            .exclude(pk=request.user.pk)
            .order_by("first_name", "id")
        )
        return self.page(
            request,
            query,
            lambda user: {"id": str(user.id), "name": user.get_full_name or "—"},
        )


class ReviewOperatorCasesView(ReviewView):
    def get(self, request):
        kind = request.query_params.get("kind", "reports")
        permission = (
            "review_eligibility" if kind == "eligibility" else "moderate_reviews"
        )
        if not request.user.has_perm(f"features.{permission}"):
            raise PermissionDenied()
        reason = text_value(request.query_params.get("reason", ""), 1000)
        if not reason:
            raise ReviewError("invalid_review_text", 400)
        if kind == "reports":
            rows = ReviewReport.objects.filter(state="open").select_related("section")
        elif kind == "appeals":
            rows = ReviewAppeal.objects.filter(state="open").select_related(
                "decision__section"
            )
        elif kind == "eligibility":
            rows = RentalOperationalCase.objects.filter(
                kind="review_eligibility", status="open"
            )
        else:
            raise NotFound()
        allowed = []
        for item in rows.order_by("created_at"):
            try:
                if kind == "eligibility":
                    if request.user.pk in {
                        item.opened_by_id,
                        getattr(item.lease, "owner_id", None),
                        getattr(item.lease, "tenant_id", None),
                        getattr(item.property, "owner_id", None),
                    }:
                        continue
                else:
                    moderation.require_moderator(
                        request.user,
                        item.section if kind == "reports" else item.decision.section,
                    )
                    if kind == "appeals" and request.user.pk in {
                        item.appellant_id,
                        item.decision.actor_id,
                    }:
                        continue
                allowed.append(item)
            except ReviewError:
                continue

        def project(item):
            submission.audit(item, request.user, "operator_case_read", reason)
            return {
                "id": str(item.id),
                "kind": kind,
                "revision": item.revision,
                "detail": getattr(item, "detail", getattr(item, "reason", "")),
                "section_id": (
                    str(item.section.id)
                    if kind == "reports"
                    else str(item.decision.section.id) if kind == "appeals" else None
                ),
                "source": item.baseline if kind == "eligibility" else None,
            }

        return self.page(request, allowed, project)


class ReviewResolveCaseView(ReviewView):
    def post(self, request, identity):
        item = (
            ReviewReport.objects.filter(id=identity).first()
            or RentalOperationalCase.objects.filter(
                id=identity, kind="review_eligibility"
            ).first()
        )
        if not item:
            raise NotFound()
        if isinstance(item, ReviewReport):
            moderation.require_moderator(request.user, item.section)
        elif not request.user.has_perm("features.review_eligibility"):
            raise PermissionDenied()
        elif request.user.pk in {
            item.opened_by_id,
            getattr(item.lease, "owner_id", None),
            getattr(item.lease, "tenant_id", None),
            getattr(item.property, "owner_id", None),
        }:
            raise ReviewError("conflict_of_interest")

        def action():
            keys(
                request.data,
                ["request_key", "expected_revision", "reason"],
                ["request_key", "expected_revision", "reason"],
            )
            locked = type(item).objects.select_for_update().get(pk=item.pk)
            revision(locked, request.data["expected_revision"])
            reason = text_value(request.data["reason"], 1000)
            if not reason:
                raise ReviewError("invalid_review_text", 400)
            if isinstance(locked, ReviewReport):
                locked.state = "resolved"
            else:
                # Resolution never creates a handover or attendance attestation.
                locked.status, locked.resolution = "resolved", reason
            locked.revision += 1
            locked.save()
            submission.audit(locked, request.user, "operator_case_resolved", reason)
            return {
                "id": str(locked.id),
                "state": "resolved",
                "revision": locked.revision,
            }

        return Response(
            submission.command(
                request.user,
                f"review.resolve_case.{identity}",
                request.data,
                action,
                item.id,
            )
        )
