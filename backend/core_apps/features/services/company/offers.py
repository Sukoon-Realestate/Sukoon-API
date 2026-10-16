from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from core_apps.properties.models import (
    Property,
    ResidentialBuilding,
    ResidentialComplex,
)
from ...company_models import PortfolioOffer
from ..rental_phase2 import RentalConflict
from ..rental_lifecycle.common import audit
from ..rental_lifecycle.inventory import (
    topology_digest,
    unit_keys,
    assert_available,
    expire_property_holds,
)
from .portfolio import units_for


def _complete(container):
    if (
        container.archived
        or container.authority_status != "verified"
        or not container.authority_reviewed_by_id
        or not container.authority_reference
    ):
        raise RentalConflict(
            "Authority over the entire asset must be reviewed.",
            code="authority_required",
        )
    if isinstance(container, ResidentialBuilding):
        if units_for(container).count() != container.declared_units:
            raise RentalConflict(
                "Register every declared residential unit before offering the entire building.",
                code="inventory_incomplete",
            )
    else:
        if (
            container.buildings.count() != container.declared_buildings
            or container.standalone_units.filter(retired_at=None).count()
            != container.declared_standalone_units
        ):
            raise RentalConflict(
                "Register the complete declared complex inventory.",
                code="inventory_incomplete",
            )
        for building in container.buildings.all():
            _complete(building)


def resolve_scope(offer, *, lock=False):
    if lock:
        # Lock the requested roots BEFORE enumerating descendants. Otherwise a
        # building inserted while we wait for a complex lock can escape locking.
        complex_ids = set()
        building_ids = set()
        if offer.scope == "entire_complex" and offer.complex_id:
            complex_ids.add(offer.complex_id)
        elif offer.scope == "entire_building" and offer.building_id:
            building_ids.add(offer.building_id)
        elif offer.scope == "selected_buildings":
            building_ids.update(offer.buildings.values_list("pk", flat=True))
        elif offer.scope == "selected_units":
            building_ids.update(
                offer.units.exclude(building=None).values_list("building_id", flat=True)
            )
            complex_ids.update(
                offer.units.exclude(complex=None).values_list("complex_id", flat=True)
            )
        complex_ids.update(
            ResidentialBuilding.objects.filter(pk__in=building_ids)
            .exclude(complex=None)
            .values_list("complex_id", flat=True)
        )
        list(
            ResidentialComplex.objects.select_for_update()
            .filter(pk__in=complex_ids)
            .order_by("pk")
        )
        if offer.scope == "entire_complex":
            building_ids.update(
                ResidentialBuilding.objects.filter(
                    complex_id=offer.complex_id
                ).values_list("pk", flat=True)
            )
        list(
            ResidentialBuilding.objects.select_for_update()
            .filter(pk__in=building_ids)
            .order_by("pk")
        )
    if offer.scope == "entire_building" and offer.building_id:
        props = units_for(offer.building)
        containers = [offer.building]
    elif offer.scope == "entire_complex" and offer.complex_id:
        props = units_for(offer.complex)
        containers = [offer.complex]
    elif offer.scope == "selected_buildings":
        containers = list(offer.buildings.all())
        props = Property.objects.filter(building__in=containers, retired_at=None)
    elif offer.scope == "selected_units":
        containers = []
        props = offer.units.all()
    else:
        raise ValidationError(
            {"scope": "Select an exact supported accommodation scope."}
        )
    ids = list(props.values_list("pk", flat=True))
    if not ids:
        raise RentalConflict(
            "The offer has no registered accommodation.", code="inventory_incomplete"
        )
    query = (
        Property.objects.select_for_update(of=("self",)) if lock else Property.objects
    )
    props = list(
        query.filter(pk__in=ids)
        .select_related("building__complex", "complex")
        .order_by("pk")
    )
    if lock:
        actual_buildings = {p.building_id for p in props if p.building_id}
        actual_complexes = {p.complex_id for p in props if p.complex_id} | {
            p.building.complex_id
            for p in props
            if p.building_id and p.building.complex_id
        }
        if not actual_buildings <= building_ids or not actual_complexes <= complex_ids:
            raise RentalConflict(
                "Inventory parents changed. Review the current scope.",
                code="stale_revision",
            )
    for container in containers:
        container.refresh_from_db()
        _complete(container)
        if container.manager_id != offer.owner_id:
            raise RentalConflict(
                "The contracting authority does not cover this asset.",
                code="authority_required",
            )
    if (
        not offer.owner.is_active
        or not offer.owner.is_verified
        or any(
            p.owner_id != offer.owner_id
            or p.retired_at is not None
            or not p.is_ownership_verified
            or not p.is_verified
            or p.status != Property.Status.VERIFIED
            for p in props
        )
    ):
        raise RentalConflict(
            "Every included unit needs reviewed authority and publication. Use separate items for different owners.",
            code="authority_required",
        )
    return props


def scope_snapshot(offer, props):
    building_ids = sorted({str(p.building.id) for p in props if p.building_id})
    complexes = {str(p.complex.id) for p in props if p.complex_id}
    complexes.update(
        str(p.building.complex.id)
        for p in props
        if p.building_id and p.building.complex_id
    )
    return {
        "scope": offer.scope,
        "offer_id": str(offer.id),
        "offer_revision": offer.revision,
        "owner_id": str(offer.owner.id),
        "building_ids": building_ids,
        "complex_ids": sorted(complexes),
        "capacity": (
            sum(p.occupancy_capacity for p in props)
            if all(p.occupancy_capacity is not None for p in props)
            else None
        ),
        "units": [
            {
                "id": str(p.id),
                "code": p.unit_code,
                "title": p.title,
                "floor": p.floor,
                "building_id": str(p.building.id) if p.building_id else None,
                "building_name": p.building.name if p.building_id else "",
                "complex_id": (
                    str(p.building.complex.id)
                    if p.building_id and p.building.complex_id
                    else str(p.complex.id) if p.complex_id else None
                ),
                "complex_name": (
                    p.building.complex.name
                    if p.building_id and p.building.complex_id
                    else p.complex.name if p.complex_id else ""
                ),
                "capacity": p.occupancy_capacity,
                "inventory_revision": (p.rental_inventory or {}).get("revision", 0),
                "topology_digest": topology_digest(p.rental_inventory),
                "physical_keys": unit_keys(p, {"rental_scope": "entire_property"}),
            }
            for p in props
        ],
        "topology_revisions": {
            str(c.id): c.topology_revision
            for c in [
                *(p.building for p in props if p.building_id),
                *(p.complex for p in props if p.complex_id),
                *(
                    p.building.complex
                    for p in props
                    if p.building_id and p.building.complex_id
                ),
            ]
        },
        "asset_revisions": {
            str(c.id): c.commercial_revision
            for c in [
                *(p.building for p in props if p.building_id),
                *(p.complex for p in props if p.complex_id),
                *(
                    p.building.complex
                    for p in props
                    if p.building_id and p.building.complex_id
                ),
            ]
        },
        "monthly_rent": {
            "amount_minor": offer.monthly_rent_minor,
            "currency": "EGP",
            "exponent": 2,
        },
        "deposit": {
            "amount_minor": offer.deposit_minor,
            "currency": "EGP",
            "exponent": 2,
        },
        "price_basis": "selected_scope",
        "billing_period": "monthly",
        "included_services": offer.included_services,
        "excluded_services": offer.excluded_services,
        "occupancy_policy": offer.occupancy_policy,
    }


@transaction.atomic
def create_offer(user, data):
    values = {
        key: data[key]
        for key in (
            "scope",
            "monthly_rent_minor",
            "deposit_minor",
            "included_services",
            "excluded_services",
            "occupancy_policy",
        )
        if key in data
    }
    for kind in ("building", "complex"):
        if data.get(kind + "_id"):
            model = ResidentialBuilding if kind == "building" else ResidentialComplex
            values[kind] = get_object_or_404(model, id=data[kind + "_id"], manager=user)
    offer = PortfolioOffer.objects.create(owner=user, **values)
    if data["scope"] == "selected_units":
        ids = data["unit_ids"]
        units = list(Property.objects.filter(id__in=ids, owner=user))
        if len(units) != len(set(ids)):
            raise ValidationError({"unit_ids": "Select only your own exact units."})
        offer.units.set(units)
    elif data["scope"] == "selected_buildings":
        ids = data["building_ids"]
        buildings = list(ResidentialBuilding.objects.filter(id__in=ids, manager=user))
        if len(buildings) != len(set(ids)):
            raise ValidationError(
                {"building_ids": "Select only your managed buildings."}
            )
        offer.buildings.set(buildings)
    if data.get("publish"):
        resolve_scope(offer, lock=True)
        offer.status = "published"
        offer.save()
    audit(offer, user, "portfolio_offer_created")
    return offer


def offer_payload(offer, *, starts_on=None, ends_on=None):
    payload = {
        "id": str(offer.id),
        "revision": offer.revision,
        "scope": offer.scope,
        "status": offer.status,
        "monthly_rent_minor": offer.monthly_rent_minor,
        "deposit_minor": offer.deposit_minor,
        "currency": "EGP",
        "exponent": 2,
        "price_basis": "selected_scope",
        "price_period": "monthly",
    }
    try:
        props = resolve_scope(offer)
        payload.update(scope_snapshot(offer, props))
        payload["eligible"] = True
        payload["available_for_dates"] = None
        if starts_on and ends_on:
            from ..rental_lifecycle.common import lifecycle_policy
            from datetime import timedelta

            _, rules = lifecycle_policy("reservations")
            for prop in props:
                assert_available(
                    prop,
                    {"rental_scope": "entire_property"},
                    starts_on,
                    ends_on + timedelta(days=rules["turnover_days"]),
                )
            payload["available_for_dates"] = True
    except RentalConflict:
        payload.update(
            eligible=False,
            available_for_dates=False if starts_on else None,
            blocking_reason="inventory_or_authority_unavailable",
        )
    return payload
