"""HTTP boundary for the bounded, sealed collective-tender pilot."""

from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from .advanced_tender_models import HousingTender, OwnerBid, PackageCandidate
from .planning_models import HousingGroup, HousingRequest
from .services.planning import (
    planning_api,
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


@planning_api(["GET"], None)
def sources(request):
    """Typed canonical source picker; no user-entered UUIDs or inferred membership."""
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
                {"id": str(g.id), "name": g.name, "roster_revision": g.roster_revision}
                for g in groups
                if not item.academic_plan_id or item.academic_plan.group_id == g.pk
            ],
        },
    )


@planning_api(["GET", "POST"], None)
def tenders(request):
    if request.method == "GET":
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
    require_planning(request.user, CAPABILITY)
    return mutate(
        request,
        "housing_tender.create",
        lambda: None,
        lambda _, revision: commands.create(request.user, request.data),
        lambda x: tender_payload(x, request.user),
        creating=True,
    )


@planning_api(["GET"], None)
def tender_detail(request, tender_id):
    return Response(tender_payload(get_tender(request.user, tender_id), request.user))


@planning_api(["POST"], CAPABILITY)
def tender_action(request, tender_id, action):
    def apply(item, revision):
        if action == "requirements":
            return commands.respond(request.user, item, request.data)
        if action == "publish":
            return commands.publish(request.user, item)
        if action == "amend":
            return commands.amend(request.user, item, request.data)
        if action == "withdraw":
            commands.require_action(request.user, item, action)
            item.status = "withdrawn"
            item.revision += 1
            item.save()
            return item
        raise NotFound()

    return mutate(
        request,
        f"housing_tender.{action}.{tender_id}",
        lambda: get_tender(request.user, tender_id, lock=True),
        apply,
        lambda x: tender_payload(x, request.user),
    )


@planning_api(["GET", "POST"], None)
def bids(request, tender_id):
    parent = get_tender(request.user, tender_id)
    if request.method == "GET":
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
    require_planning(request.user, CAPABILITY)
    return mutate(
        request,
        f"housing_bid.create.{tender_id}",
        lambda: get_tender(request.user, tender_id, lock=True),
        lambda item, revision: commands.bid(request, item),
        lambda x: bid_payload(x, request.user),
        creating=True,
    )


@planning_api(["POST"], CAPABILITY)
def withdraw_bid(request, bid_id):
    def load():
        item = get_object_or_404(OwnerBid, id=bid_id, owner=request.user)
        get_tender(request.user, item.tender.id, lock=True)
        return OwnerBid.objects.select_for_update().get(pk=item.pk)

    def apply(item, revision):
        if item.status != "submitted":
            raise PermissionDenied("This quote can no longer be withdrawn.")
        item.status = "withdrawn"
        item.revision += 1
        item.save()
        return item

    return mutate(
        request,
        f"housing_bid.withdraw.{bid_id}",
        load,
        apply,
        lambda x: bid_payload(x, request.user),
    )


@planning_api(["GET", "POST"], None)
def packages(request, tender_id):
    parent = get_tender(request.user, tender_id)
    if not member(request.user, parent):
        raise NotFound()
    if request.method == "GET":
        return page(
            request,
            parent.packages.select_related(
                "tender__group", "tender__request", "snapshot"
            ).order_by("-created_at", "pkid"),
            lambda x: package_payload(x, request.user),
        )
    require_planning(request.user, CAPABILITY)
    return mutate(
        request,
        f"housing_package.create.{tender_id}",
        lambda: get_tender(request.user, tender_id, lock=True),
        lambda item, revision: commands.package(request, item),
        lambda x: package_payload(x, request.user),
        creating=True,
    )


@planning_api(["GET"], None)
def package_detail(request, package_id):
    return Response(
        package_payload(get_package(request.user, package_id), request.user)
    )


@planning_api(["POST"], CAPABILITY)
def package_consent(request, package_id):
    return mutate(
        request,
        f"housing_package.consent.{package_id}",
        lambda: get_package(request.user, package_id, lock=True),
        lambda item, revision: commands.consent(request, item),
        lambda x: package_payload(x, request.user),
    )


@planning_api(["POST"], None)
def prepare_package(request, package_id):
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


@planning_api(["GET", "POST"], None)
def construction_runs(request, tender_id):
    from .services.housing_tenders import construction

    tender = get_tender(request.user, tender_id)
    if not admin(request.user, tender):
        raise NotFound()
    if request.method == "GET":
        return page(
            request,
            tender.package_runs.order_by("-created_at", "pkid"),
            lambda item: construction.payload(item, request.user),
        )
    require_planning(request.user, CAPABILITY)
    return mutate(
        request,
        f"housing_tender.construct.{tender_id}",
        lambda: get_tender(request.user, tender_id, lock=True),
        lambda item, _: construction.create(request, item),
        lambda item: construction.payload(item, request.user),
        creating=True,
    )


@planning_api(["GET"], None)
def construction_detail(request, run_id):
    from .services.housing_tenders.construction import get_run, payload

    return Response(payload(get_run(request.user, run_id), request.user))


@planning_api(["POST"], CAPABILITY)
def construction_retry(request, run_id):
    from django.db import transaction
    from .services.housing_tenders.construction import get_run, payload
    from .services.housing_tenders.jobs import enqueue

    def apply(item, _):
        if item.status != "queued":
            raise PermissionDenied(
                "Only a queued package search can be dispatched again."
            )
        item.revision += 1
        item.save(update_fields=["revision", "updated_at"])
        transaction.on_commit(lambda: enqueue(str(item.id)))
        return item

    return mutate(
        request,
        f"housing_tender.dispatch.{run_id}",
        lambda: get_run(request.user, run_id, lock=True),
        apply,
        lambda item: payload(item, request.user),
    )


@planning_api(["GET", "POST"], None)
def clarifications(request, bid_id):
    from .advanced_tender_models import TenderBidClarification
    from .services.planning import check_revision, text_field
    from .services.housing_tenders.access import subject

    def serialize(item):
        return {
            "id": str(item.id),
            "revision": 1,
            "bid_id": str(item.bid.id),
            "bid_revision": item.bid_revision,
            "text": item.text,
            "author_role": (
                "owner" if item.author_id == item.bid.owner_id else "coordinator"
            ),
            "created_at": item.created_at.isoformat(),
            "amends_terms": False,
        }

    def load():
        item = get_object_or_404(OwnerBid.objects.select_related("tender"), id=bid_id)
        subject(request.user, item.id)
        return item

    item = load()
    if request.method == "GET":
        return page(
            request,
            item.clarifications.select_related("bid").order_by("created_at", "pkid"),
            serialize,
        )
    require_planning(request.user, CAPABILITY)

    def apply(item, _):
        check_revision(item.revision, request.data.get("bid_revision"))
        return TenderBidClarification.objects.create(
            bid=item,
            author=request.user,
            bid_revision=item.revision,
            text=text_field(request.data, "text", required=True, limit=1600),
        )

    return mutate(
        request,
        f"housing_bid.clarification.{bid_id}",
        load,
        apply,
        serialize,
        creating=True,
    )
