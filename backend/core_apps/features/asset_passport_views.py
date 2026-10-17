from django.db.models import Q
from rest_framework.response import Response
from .asset_passport_models import AssetItem
from .services.planning import planning_api, page, mutate, require_planning
from .services.asset_passport import access, commands, projections, evidence
from core_apps.properties.models import Property

CAPABILITY = "asset_passport"


@planning_api(["GET"], None)
def asset_spaces(request, property_id):
    prop = access.property_for(request.user, property_id, write=True)
    return page(
        request,
        (prop.rental_inventory or {}).get("rooms", []),
        lambda room: {"id": str(room["id"]), "title": room.get("name", "")},
    )


@planning_api(["GET"], None)
def asset_destinations(request):
    return page(
        request,
        Property.objects.filter(owner=request.user, retired_at=None).order_by(
            "title", "id"
        ),
        lambda prop: {"id": str(prop.id), "title": prop.title},
    )


@planning_api(["GET", "POST"], None)
def asset_items(request, property_id):
    lease_id = request.query_params.get("lease_id", "")
    prop = access.property_for(
        request.user, property_id, write=request.method == "POST", lease_id=lease_id
    )
    if request.method == "GET":
        query = (
            AssetItem.objects.filter(locations__property=prop)
            .distinct()
            .order_by("label", "id")
        )
        if prop.owner_id != request.user.pk:
            lease = access.leases_for(request.user).get(id=lease_id, property=prop)
            query = (
                query.filter(locations__starts_on__lt=lease.end_date)
                .filter(
                    Q(locations__ends_on_exclusive=None)
                    | Q(locations__ends_on_exclusive__gt=lease.start_date)
                )
                .distinct()
            )
            query = [
                item
                for item in query
                if access.periods_for(request.user, item, lease_id)
            ]
        return page(
            request,
            query,
            lambda item: projections.payload(
                item, request.user, detailed=False, lease_id=lease_id
            ),
        )
    require_planning(request.user, CAPABILITY)
    return mutate(
        request,
        "asset.create",
        lambda: access.property_for(request.user, property_id, write=True, lock=True),
        lambda prop, _: commands.register(request.user, prop, request.data),
        lambda item: projections.payload(item, request.user),
        creating=True,
    )


@planning_api(["GET"], None)
def asset_detail(request, asset_id):
    lease_id = request.query_params.get("lease_id", "")
    return Response(
        projections.payload(
            access.asset_for(request.user, asset_id, lease_id=lease_id),
            request.user,
            lease_id=lease_id,
        )
    )


@planning_api(["POST"], None)
def asset_action(request, asset_id, action):
    require_planning(request.user, CAPABILITY)
    return mutate(
        request,
        "asset." + action,
        lambda: access.asset_for(
            request.user, asset_id, write=action != "observations", lock=True
        ),
        lambda item, _: (
            commands.observe(request.user, item, request.data)
            if action == "observations"
            else (
                commands.update(request.user, item, request.data)
                if action == "update"
                else commands.lifecycle(request.user, item, action, request.data)
            )
        ),
        lambda item: projections.payload(item, request.user),
    )


@planning_api(["GET"], None)
def asset_sources(request, asset_id):
    item = access.asset_for(request.user, asset_id)
    leases = access.leases_for(request.user).filter(
        property_id__in=item.locations.values("property_id")
    )
    if request.query_params.get("lease_id"):
        leases = leases.filter(id=request.query_params["lease_id"])
    rows = []
    for kind, model in evidence.SOURCES.items():
        query = model.objects.filter(lease__in=leases).select_related("lease")
        if kind == "condition_report":
            query = query.exclude(Q(status="draft") & ~Q(author=request.user))
        rows += [(kind, row) for row in query]
    rows.sort(key=lambda pair: (pair[1].created_at, str(pair[1].id)), reverse=True)
    return page(
        request,
        rows,
        lambda pair: evidence.source_payload(pair[1], pair[0], request.user),
    )
