from functools import partial
from .services.housing_tenders import entry_commands as entry_commands

"""HTTP boundary for the bounded, sealed collective-tender pilot."""

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer


from django.db.models import Q, F
from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from .advanced_tender_models import HousingTender
from .planning_models import HousingGroup, HousingRequest
from .services.planning import (
    require_planning,
    mutate,
    page,
    eligible_owner,
    enabled_services,
)
from .services.housing_tenders import commands
from .services.housing_tenders.access import (
    CAPABILITY,
    admin,
    member,
    get_tender,
    get_package,
)
from .services.housing_tenders.projections import (
    tender_payload,
    bid_payload,
    package_payload,
)


class SourcesView(FeatureAPIView):
    "Typed canonical source picker; no user-entered UUIDs or inferred membership."
    name = "Sources"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "advanced_tender_views",
            "sources",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        groups = HousingGroup.objects.filter(
            status="active",
            memberships__user=request.user,
            memberships__status="active",
            memberships__role="admin",
        )
        if request.query_params.get("group_id"):
            groups = groups.filter(id=request.query_params["group_id"])
        demand = (
            HousingRequest.objects.filter(
                user=request.user, status="published", expires_at__gt=timezone.now()
            )
            .filter(Q(academic_plan__isnull=True) | Q(academic_plan__group__in=groups))
            .select_related("academic_plan")
        )
        if not groups.exists():
            demand = demand.none()
        return page(
            request,
            demand.order_by("-created_at", "pkid"),
            lambda item: {
                "id": str(item.id),
                "title": item.title,
                "revision": item.revision,
                "groups": [
                    {
                        "id": str(g.id),
                        "name": g.name,
                        "roster_revision": g.roster_revision,
                    }
                    for g in groups
                    if not item.academic_plan_id or item.academic_plan.group_id == g.pk
                ],
            },
        )


# Stable callable import for integrations; URLs use the explicit class.
sources = SourcesView.as_view()


class TendersView(FeatureAPIView):
    name = "Tenders"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "advanced_tender_views",
            "tenders",
            boundary="planning",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "advanced_tender_views",
            "tenders",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        memberships = HousingGroup.objects.filter(
            memberships__user=request.user, memberships__status="active"
        )
        candidates = HousingTender.objects.filter(group__in=memberships).select_related(
            "group"
        )
        items = HousingTender.objects.filter(
            pk__in=[x.pk for x in candidates if member(request.user, x)]
        )
        if request.query_params.get("owner") == "true":
            authorized = Q(bids__owner=request.user)
            if CAPABILITY in enabled_services() and eligible_owner(request.user):
                authorized |= Q(
                    status="published",
                    closes_at__gt=timezone.now(),
                    group__status="active",
                    group__roster_revision=F("roster_revision"),
                    request__revision=F("request_revision"),
                    request__status="published",
                    request__expires_at__gt=timezone.now(),
                )
            items = HousingTender.objects.filter(authorized).distinct()
        if request.query_params.get("group_id"):
            items = items.filter(group__id=request.query_params["group_id"])
        return page(
            request,
            items.select_related("group", "request", "active_snapshot").order_by(
                "-created_at", "pkid"
            ),
            lambda x: tender_payload(x, request.user),
        )

    def post(self, request):
        require_planning(request.user, CAPABILITY)
        return mutate(
            request,
            "housing_tender.create",
            lambda: None,
            lambda _, revision: commands.create(request.user, request.data),
            lambda x: tender_payload(x, request.user),
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
tenders = TendersView.as_view()


class TenderDetailView(FeatureAPIView):
    name = "Tender Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "advanced_tender_views",
            "tender_detail",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, tender_id):
        return Response(
            tender_payload(get_tender(request.user, tender_id), request.user)
        )


# Stable callable import for integrations; URLs use the explicit class.
tender_detail = TenderDetailView.as_view()


class TenderActionView(FeatureAPIView):
    name = "Tender Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "advanced_tender_views",
            "tender_action",
            boundary="planning",
            capability=CAPABILITY,
            typed=False,
        ),
    }

    def post(self, request, tender_id, action):
        apply = partial(
            entry_commands.tender_action_post_apply,
            action=action,
            actor=request.user,
            receipt_data=request.data,
        )

        return mutate(
            request,
            f"housing_tender.{action}.{tender_id}",
            lambda: get_tender(request.user, tender_id, lock=True),
            apply,
            lambda x: tender_payload(x, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
tender_action = TenderActionView.as_view()


class BidsView(FeatureAPIView):
    name = "Bids"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "advanced_tender_views",
            "bids",
            boundary="planning",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "advanced_tender_views",
            "bids",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, tender_id):
        parent = get_tender(request.user, tender_id)
        items = (
            parent.bids.all()
            if admin(request.user, parent)
            else parent.bids.filter(owner=request.user)
        )
        return page(
            request,
            items.select_related(
                "tender__group", "tender__request", "snapshot"
            ).order_by("-created_at", "pkid"),
            lambda x: bid_payload(x, request.user),
        )

    def post(self, request, tender_id):
        get_tender(request.user, tender_id)
        require_planning(request.user, CAPABILITY)
        return mutate(
            request,
            f"housing_bid.create.{tender_id}",
            lambda: get_tender(request.user, tender_id, lock=True),
            lambda item, revision: commands.bid(request, item),
            lambda x: bid_payload(x, request.user),
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
bids = BidsView.as_view()


class WithdrawBidView(FeatureAPIView):
    name = "Withdraw Bid"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "advanced_tender_views",
            "withdraw_bid",
            boundary="planning",
            capability=CAPABILITY,
            typed=False,
        ),
    }

    def post(self, request, bid_id):
        load = partial(
            entry_commands.withdraw_bid_post_load, actor=request.user, bid_id=bid_id
        )

        apply = partial(entry_commands.withdraw_bid_post_apply)

        return mutate(
            request,
            f"housing_bid.withdraw.{bid_id}",
            load,
            apply,
            lambda x: bid_payload(x, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
withdraw_bid = WithdrawBidView.as_view()


class PackagesView(FeatureAPIView):
    name = "Packages"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "advanced_tender_views",
            "packages",
            boundary="planning",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "advanced_tender_views",
            "packages",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, tender_id):
        parent = get_tender(request.user, tender_id)
        if not member(request.user, parent):
            raise NotFound()
        return page(
            request,
            parent.packages.select_related(
                "tender__group", "tender__request", "snapshot"
            ).order_by("-created_at", "pkid"),
            lambda x: package_payload(x, request.user),
        )

    def post(self, request, tender_id):
        parent = get_tender(request.user, tender_id)
        if not member(request.user, parent):
            raise NotFound()
        require_planning(request.user, CAPABILITY)
        return mutate(
            request,
            f"housing_package.create.{tender_id}",
            lambda: get_tender(request.user, tender_id, lock=True),
            lambda item, revision: commands.package(request, item),
            lambda x: package_payload(x, request.user),
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
packages = PackagesView.as_view()


class PackageDetailView(FeatureAPIView):
    name = "Package Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "advanced_tender_views",
            "package_detail",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, package_id):
        return Response(
            package_payload(get_package(request.user, package_id), request.user)
        )


# Stable callable import for integrations; URLs use the explicit class.
package_detail = PackageDetailView.as_view()


class PackageConsentView(FeatureAPIView):
    name = "Package Consent"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "advanced_tender_views",
            "package_consent",
            boundary="planning",
            capability=CAPABILITY,
            typed=False,
        ),
    }

    def post(self, request, package_id):
        return mutate(
            request,
            f"housing_package.consent.{package_id}",
            lambda: get_package(request.user, package_id, lock=True),
            lambda item, revision: commands.consent(request, item),
            lambda x: package_payload(x, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
package_consent = PackageConsentView.as_view()


class PreparePackageView(FeatureAPIView):
    name = "Prepare Package"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "advanced_tender_views",
            "prepare_package",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, package_id):
        from .services.housing_tenders.execution import build
        from .services.advanced_execution.projections import payload

        require_planning(request.user, "collective_tender_execution")
        return mutate(
            request,
            f"housing_package.prepare.{package_id}",
            lambda: get_package(request.user, package_id, lock=True),
            lambda item, _: build(request.user, item, request.data),
            lambda item: payload(item, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
prepare_package = PreparePackageView.as_view()


class ConstructionRunsView(FeatureAPIView):
    name = "Construction Runs"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "advanced_tender_views",
            "construction_runs",
            boundary="planning",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "advanced_tender_views",
            "construction_runs",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, tender_id):
        from .services.housing_tenders import construction

        tender = get_tender(request.user, tender_id)
        if not admin(request.user, tender):
            raise NotFound()
        return page(
            request,
            tender.package_runs.order_by("-created_at", "pkid"),
            lambda item: construction.payload(item, request.user),
        )

    def post(self, request, tender_id):
        from .services.housing_tenders import construction

        tender = get_tender(request.user, tender_id)
        if not admin(request.user, tender):
            raise NotFound()
        require_planning(request.user, CAPABILITY)
        return mutate(
            request,
            f"housing_tender.construct.{tender_id}",
            lambda: get_tender(request.user, tender_id, lock=True),
            lambda item, _: construction.create(request, item),
            lambda item: construction.payload(item, request.user),
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
construction_runs = ConstructionRunsView.as_view()


class ConstructionDetailView(FeatureAPIView):
    name = "Construction Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "advanced_tender_views",
            "construction_detail",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, run_id):
        from .services.housing_tenders.construction import get_run, payload

        return Response(payload(get_run(request.user, run_id), request.user))


# Stable callable import for integrations; URLs use the explicit class.
construction_detail = ConstructionDetailView.as_view()


class ConstructionRetryView(FeatureAPIView):
    name = "Construction Retry"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "advanced_tender_views",
            "construction_retry",
            boundary="planning",
            capability=CAPABILITY,
            typed=False,
        ),
    }

    def post(self, request, run_id):
        from django.db import transaction
        from .services.housing_tenders.construction import get_run, payload
        from .services.housing_tenders.jobs import enqueue

        apply = partial(
            entry_commands.construction_retry_post_apply,
            enqueue=enqueue,
            transaction=transaction,
        )

        return mutate(
            request,
            f"housing_tender.dispatch.{run_id}",
            lambda: get_run(request.user, run_id, lock=True),
            apply,
            lambda item: payload(item, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
construction_retry = ConstructionRetryView.as_view()


class ClarificationsView(FeatureAPIView):
    name = "Clarifications"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "advanced_tender_views",
            "clarifications",
            boundary="planning",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "advanced_tender_views",
            "clarifications",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, bid_id):
        from .services.housing_tenders.access import subject

        serialize = partial(entry_commands.clarifications_get_serialize)
        load = partial(
            entry_commands.clarifications_get_load,
            actor=request.user,
            bid_id=bid_id,
            subject=subject,
        )
        item = load()
        return page(
            request,
            item.clarifications.select_related("bid").order_by("created_at", "pkid"),
            serialize,
        )

    def post(self, request, bid_id):
        from .advanced_tender_models import TenderBidClarification
        from .services.planning import check_revision, text_field
        from .services.housing_tenders.access import subject

        serialize = partial(entry_commands.clarifications_post_serialize)
        load = partial(
            entry_commands.clarifications_post_load,
            actor=request.user,
            bid_id=bid_id,
            subject=subject,
        )
        load()
        require_planning(request.user, CAPABILITY)
        apply = partial(
            entry_commands.clarifications_post_apply,
            TenderBidClarification=TenderBidClarification,
            actor=request.user,
            check_revision=check_revision,
            receipt_data=request.data,
            text_field=text_field,
        )
        return mutate(
            request,
            f"housing_bid.clarification.{bid_id}",
            load,
            apply,
            serialize,
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
clarifications = ClarificationsView.as_view()
