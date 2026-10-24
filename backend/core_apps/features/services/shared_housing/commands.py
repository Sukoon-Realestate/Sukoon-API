"""Commands use shared_mutate root locks and planning.mutate receipts."""

from datetime import timedelta
from django.conf import settings
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied
from ...planning_models import RoommateConnection
from ...shared_housing_models import (
    SharedHousingPlan,
    SharedHousingProposal,
    SharedHousingAllocation,
    SharedHousingConsent,
)
from ...models import TermsProposal, RentalInterest
from ..planning import text_field, civil_date
from ..rental_phase2 import RentalConflict, fingerprint, assert_owner_ready
from ..rental_application_records import (
    create_interest,
    create_terms,
    create_invitation,
)
from ..rental_lifecycle.consents import record_consent
from ..rental_lifecycle.terms import validate_terms_offer, _json_safe
from ..tenancy_invitations import (
    resolve_offer_snapshot,
    create_notification_for_invitation,
)
from .access import members, member_ids, is_member, require_action
from .validation import criteria, validate_pair


def create(request):
    connection = get_object_or_404(
        RoommateConnection.objects.select_for_update(),
        id=request.data.get("connection_id"),
        status="accepted",
    )
    if request.user.pk not in {connection.first_id, connection.second_id}:
        raise PermissionDenied("Only connection participants can create a plan.")
    from core_apps.chat.moderation.policy import require_business_participants

    require_business_participants(connection.first, connection.second)
    current = (
        SharedHousingPlan.objects.filter(connection=connection)
        .exclude(status__in=["closed", "handed_off"])
        .first()
    )
    if current and current.expires_at <= timezone.now():
        close_proposals(current)
        current.status, current.published = "closed", False
        audit(current, request.user, "expired")
        current = None
    if current:
        return current
    plan = SharedHousingPlan(
        connection=connection,
        coordinator=request.user,
        expires_at=timezone.now() + timedelta(days=settings.PLANNING_REQUEST_TTL_DAYS),
    )
    plan.criteria = criteria(request.data.get("criteria"), plan)
    plan.save()
    return plan


def audit(plan, actor, action):
    plan.revision += 1
    plan.history = [
        *plan.history,
        {
            "actor_id": str(actor.id),
            "action": action,
            "revision": plan.revision,
            "at": timezone.now().isoformat(),
        },
    ]
    plan.save()
    return plan


def close_proposals(plan, *, status="superseded", keep=None):
    for proposal in plan.proposals.exclude(
        status__in=["handed_off", "rejected", "superseded"]
    ).exclude(pk=keep):
        for allocation in proposal.allocations.select_related("interest", "terms"):
            if allocation.interest_id:
                RentalInterest.objects.filter(pk=allocation.interest_id).update(
                    status="withdrawn", waiting_for="", revision=F("revision") + 1
                )
            if allocation.terms_id:
                TermsProposal.objects.filter(pk=allocation.terms_id).update(
                    status="superseded", accepted_by=[], revision=F("revision") + 1
                )
        proposal.status = status
        proposal.revision += 1
        proposal.save()


def plan_action(request, plan, action):
    require_action(plan, request.user, action)
    if action not in {"withdraw", "decline_invite", "unpublish"}:
        from core_apps.chat.moderation.policy import require_business_participants

        require_business_participants(*members(plan))
    if action in {"withdraw", "decline_invite"}:
        close_proposals(plan)
        plan.status, plan.published = "closed", False
    elif action == "accept_invite":
        plan.status = "searching"
    elif action == "edit":
        plan.criteria = criteria(request.data.get("criteria"), plan)
        close_proposals(plan)
        plan.publication_consents, plan.published = [], False
    elif action == "approve_publication":
        if request.data.get("consent") is not True:
            raise ValidationError(
                {"consent": "Explicit publication consent is required."}
            )
        plan.publication_consents = sorted(
            set(plan.publication_consents) | {str(request.user.id)}
        )
    elif action == "publish":
        if set(plan.publication_consents) != member_ids(plan):
            raise RentalConflict(
                "Both participants must approve publication.", code="consent_required"
            )
        civil_date(plan.criteria["start_on"], future=True)
        plan.published = True
    elif action == "unpublish":
        plan.published = False
    else:
        raise ValidationError({"action": "Unsupported plan action."})
    return audit(plan, request.user, action)


def propose(request, plan):
    require_action(plan, request.user, "propose")
    prop, lines = validate_pair(
        request,
        plan,
        request.data.get("allocations"),
        owned=not is_member(plan, request.user),
    )
    proposal = SharedHousingProposal.objects.create(
        plan=plan,
        property=prop,
        creator=request.user,
        note=text_field(request.data, "note"),
    )
    for line in lines:
        tenant = next(
            user for user in members(plan) if str(user.id) == line["tenant_id"]
        )
        SharedHousingAllocation.objects.create(
            proposal=proposal, tenant=tenant, selection=line["selection"]
        )
    return audit(plan, request.user, "propose")


def snapshot(proposal):
    return {
        "criteria": proposal.plan.criteria,
        "allocations": [
            {
                "tenant_id": str(row.tenant.id),
                "selection": row.selection,
                "terms": row.terms.terms if row.terms_id else None,
            }
            for row in proposal.allocations.select_related("tenant", "terms").order_by(
                "tenant_id"
            )
        ],
        "independent_contracts": True,
    }


def consent(proposal, actor, kind):
    value = snapshot(proposal)
    SharedHousingConsent.objects.get_or_create(
        proposal=proposal,
        actor=actor,
        revision=proposal.revision,
        kind=kind,
        defaults={"digest": fingerprint(value), "snapshot": value},
    )


def consented(proposal, kind):
    return set(
        str(value)
        for value in proposal.consents.filter(
            revision=proposal.revision,
            kind=kind,
            digest=fingerprint(snapshot(proposal)),
        ).values_list("actor__id", flat=True)
    )


def revalidate(request, proposal):
    return validate_pair(
        request,
        proposal.plan,
        [
            {"tenant_id": str(row.tenant.id), "selection": row.selection}
            for row in proposal.allocations.select_related("tenant")
        ],
    )


def proposal_action(request, plan, identifier, action):
    require_action(plan, request.user, action)
    if action in {"owner_accept", "consent_terms", "send_invitations"}:
        from ...providers import require_rental_provider

        require_rental_provider(request.user)
    proposal = get_object_or_404(
        plan.proposals.select_related("property__owner"), id=identifier
    )
    if (
        not is_member(plan, request.user)
        and proposal.property.owner_id != request.user.pk
    ):
        raise PermissionDenied("Only this property's owner can review the proposal.")
    rows = list(
        proposal.allocations.select_related(
            "tenant", "interest", "terms", "invitation"
        ).order_by("tenant_id")
    )
    if len(rows) != 2:
        raise RentalConflict("The proposal has incomplete allocations.")
    if action == "consent_selection":
        if proposal.status != "candidate" or request.data.get("consent") is not True:
            raise RentalConflict("Review the current candidate before accepting.")
        revalidate(request, proposal)
        consent(proposal, request.user, "selection")
    elif action == "submit":
        if proposal.status != "candidate" or consented(
            proposal, "selection"
        ) != member_ids(plan):
            raise RentalConflict(
                "Both participants must approve this exact proposal.",
                code="consent_required",
            )
        prop, _ = revalidate(request, proposal)
        close_proposals(plan, keep=proposal.pk)
        for row in rows:
            _, canonical = resolve_offer_snapshot(
                prop,
                row.selection["offer_id"],
                row.selection["offer_revision"],
                request,
            )
            row.interest = create_interest(
                property=prop,
                tenant=row.tenant,
                offer_id=row.selection["offer_id"],
                offer_revision=row.selection["offer_revision"],
                offer_snapshot=canonical,
                desired_start=civil_date(plan.criteria["start_on"]),
                desired_end=civil_date(plan.criteria["end_on"]),
                months=plan.criteria["months"],
                occupants=1,
                message=proposal.note,
                response_due_at=timezone.now() + timedelta(hours=48),
            )
            row.save()
        proposal.status, plan.status, plan.published = "submitted", "reviewing", False
        proposal.save()
    elif action == "owner_accept":
        if proposal.status != "submitted":
            raise RentalConflict("Only a submitted pair can be accepted.")
        assert_owner_ready(request.user, proposal.property)
        revalidate(request, proposal)
        from ...rental_serializers_parts.owner_payment_profile_serializer import (
            RentalTermsSerializer,
        )
        from ..planning import offer_money

        terms = request.data.get("allocation_terms")
        if (
            not isinstance(terms, list)
            or len(terms) != 2
            or any(
                not isinstance(v, dict)
                or not isinstance(v.get("tenant_id"), str)
                or not isinstance(v.get("terms"), dict)
                for v in terms
            )
            or {v["tenant_id"] for v in terms} != member_ids(plan)
        ):
            raise ValidationError(
                {"allocation_terms": "Supply reviewed terms for both participants."}
            )
        for row in rows:
            raw = next(
                value["terms"]
                for value in terms
                if value["tenant_id"] == str(row.tenant.id)
            )
            serializer = RentalTermsSerializer(data=raw)
            serializer.is_valid(raise_exception=True)
            value = serializer.validated_data
            validate_terms_offer(value, row.selection)
            _, deposit = offer_money(row.selection)
            if (
                str(value["starts_on"]) != plan.criteria["start_on"]
                or str(value["ends_on_exclusive"]) != plan.criteria["end_on"]
                or value["occupants"] != 1
                or value["deposit"]["amount_minor"] != deposit
            ):
                raise ValidationError(
                    {
                        "terms": "Preserve the reviewed dates, individual occupancy and deposit."
                    }
                )
            row.terms = create_terms(
                interest=row.interest,
                owner=request.user,
                terms=_json_safe(value),
                snapshot=row.interest.offer_snapshot,
            )
            row.save()
        proposal.status, proposal.revision = "terms", proposal.revision + 1
        proposal.save()
    elif action == "consent_terms":
        if (
            proposal.status != "terms"
            or request.data.get("independent_consent") is not True
        ):
            raise ValidationError(
                {
                    "independent_consent": "Explicit consent to independent contracting is required."
                }
            )
        revalidate(request, proposal)
        row = next(value for value in rows if value.tenant_id == request.user.pk)
        record_consent(row.terms, request.user, "accept")
        row.terms.accepted_by = sorted(
            {str(request.user.id), str(proposal.property.owner.id)}
        )
        row.terms.status = "accepted"
        row.terms.revision += 1
        row.terms.save()
        consent(proposal, request.user, "independent")
    elif action == "send_invitations":
        if proposal.status != "terms" or consented(
            proposal, "independent"
        ) != member_ids(plan):
            raise RentalConflict(
                "Both participants must approve independent contracts.",
                code="consent_required",
            )
        assert_owner_ready(request.user, proposal.property)
        revalidate(request, proposal)
        for row in rows:
            if row.terms.status != "accepted":
                raise RentalConflict("Both current terms must be accepted.")
            # Preserve the exact canonical wire snapshot expected by invitation eligibility.
            _, canonical = resolve_offer_snapshot(
                proposal.property,
                row.selection["offer_id"],
                row.selection["offer_revision"],
                request,
            )
            row.invitation = create_invitation(
                interest=row.interest,
                proposal=row.terms,
                owner=request.user,
                snapshot=canonical,
            )
            row.save()
            create_notification_for_invitation(request, row.invitation)
        proposal.status, plan.status = "handed_off", "handed_off"
        proposal.save()
    elif action in {"owner_reject", "request_changes"}:
        proposal.note = text_field(request.data, "note", required=True)
        proposal.save(update_fields=["note", "updated_at"])
        if proposal.status not in {"submitted", "terms"}:
            raise RentalConflict("This proposal is no longer under joint review.")
        close_proposals(
            plan, status="rejected" if action == "owner_reject" else "superseded"
        )
        plan.status = "searching"
    else:
        raise ValidationError({"action": "Unsupported proposal action."})
    return audit(plan, request.user, action)


def connection_closed(connection, actor):
    for plan in (
        SharedHousingPlan.objects.select_for_update()
        .filter(connection=connection)
        .exclude(status__in=["closed", "handed_off"])
    ):
        close_proposals(plan)
        plan.status, plan.published = "closed", False
        audit(plan, actor, "connection_closed")
        from .projections import record_event

        record_event(plan, actor, "connection_closed")
