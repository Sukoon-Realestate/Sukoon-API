"""Hierarchy mutations lock parents before units; allocations use identical order."""

from copy import deepcopy
import uuid
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from core_apps.properties.models import (
    Property,
    ResidentialBuilding,
    ResidentialComplex,
    PortfolioBatchItem,
)
from core_apps.properties.services.property import PropertyService
from core_apps.properties.rental_inventory import normalize_inventory
from core_apps.users.models import User
from ...company_models import CompanyBookingItem
from ..rental_lifecycle.common import audit, require_revision
from ..rental_phase2 import RentalConflict, fingerprint


def units_for(container):
    if isinstance(container, ResidentialBuilding):
        return Property.objects.filter(building=container, retired_at=None)
    return Property.objects.filter(
        Q(complex=container) | Q(building__complex=container)
    ).filter(retired_at=None)


def parent_for(user, kind, identity, lock=False):
    if kind not in {"building", "complex"}:
        raise ValidationError("Choose building or complex.")
    model = ResidentialBuilding if kind == "building" else ResidentialComplex
    expected_root = None
    if lock and kind == "building":
        root = get_object_or_404(model, id=identity, manager=user, archived=False)
        expected_root = root.complex_id
        if root.complex_id:
            ResidentialComplex.objects.select_for_update().get(pk=root.complex_id)
    query = model.objects.select_for_update() if lock else model.objects
    parent = get_object_or_404(query, id=identity, manager=user, archived=False)
    if lock and kind == "building" and parent.complex_id != expected_root:
        raise RentalConflict(
            "The parent changed. Create a fresh inventory preview.",
            code="stale_revision",
        )
    return parent


def assert_topology_mutable(container):
    # Historical schedule remains immutable. Block scope changes while any live
    # aggregate hold/contract references this parent, including unknown payments.
    items = CompanyBookingItem.objects.filter(
        Q(hold__status__in=["active", "reconciliation_pending", "committed"])
        | Q(
            lease__status__in=[
                "draft",
                "pending_signatures",
                "signed",
                "active",
                "termination_pending",
            ]
        )
    )
    key = (
        "building_ids" if isinstance(container, ResidentialBuilding) else "complex_ids"
    )
    if any(str(container.id) in item.snapshot.get(key, []) for item in items):
        raise RentalConflict(
            "An existing company commitment protects this inventory topology.",
            code="inventory_conflict",
        )
    if isinstance(container, ResidentialBuilding) and container.complex_id:
        assert_topology_mutable(container.complex)


@transaction.atomic
def create_container(user, data):
    values = {
        k: data[k]
        for k in ("name", "code", "address", "description", "facilities")
        if k in data
    }
    values.update(data.get("facts", {}))
    if data["kind"] == "building":
        parent = None
        if data.get("complex_id"):
            parent = parent_for(user, "complex", data["complex_id"], lock=True)
            assert_topology_mutable(parent)
        item = ResidentialBuilding.objects.create(
            manager=user,
            complex=parent,
            declared_units=data["declared_units"],
            floors=data.get("floors"),
            **values
        )
        if parent:
            parent.topology_revision += 1
            parent.revision += 1
            parent.save()
    else:
        item = ResidentialComplex.objects.create(
            manager=user,
            declared_buildings=data["declared_buildings"],
            declared_standalone_units=data["declared_standalone_units"],
            **values
        )
    audit(item, user, "residential_container_created")
    return item


@transaction.atomic
def attach_unit(user, kind, identity, data):
    """Attach the original unit identity. Reparenting commitments is not a form edit."""
    parent = parent_for(user, kind, identity, lock=True)
    require_revision(parent, data["expected_revision"])
    assert_topology_mutable(parent)
    prop = get_object_or_404(
        Property.objects.select_for_update(),
        id=data["property_id"],
        owner=user,
        retired_at=None,
    )
    if (prop.rental_inventory or {}).get("revision", 0) != data["inventory_revision"]:
        raise RentalConflict(
            "Reload the unit inventory before attaching it.", code="stale_revision"
        )
    if prop.building_id or prop.complex_id:
        raise RentalConflict(
            "This unit already belongs to an asset. Reparenting requires a controlled change.",
            code="reparenting_required",
        )
    if (
        prop.rental_day_locks.exists()
        or prop.digital_leases.filter(
            status__in=[
                "draft",
                "pending",
                "pending_signatures",
                "signed",
                "active",
                "termination_pending",
            ]
        ).exists()
    ):
        raise RentalConflict(
            "Resolve active unit commitments before changing its parent or capacity.",
            code="inventory_conflict",
        )
    setattr(prop, kind, parent)
    prop.unit_code = data["unit_code"]
    prop.occupancy_capacity = data["occupancy_capacity"]
    prop.save(update_fields=[kind, "unit_code", "occupancy_capacity", "updated_at"])
    parent.revision += 1
    parent.topology_revision += 1
    parent.save()
    audit(
        prop,
        user,
        "portfolio_existing_unit_attached",
        metadata={
            "parent_kind": kind,
            "parent_id": str(parent.id),
            "unit_code": prop.unit_code,
        },
    )
    return parent


def cloned_inventory(source):
    """Copy layout and terms, never physical identities, availability or evidence."""
    raw = source.rental_inventory or {}
    if not raw:
        return {}
    identity = {}
    rooms = []
    for old in raw.get("rooms", []):
        key = str(uuid.uuid4())
        identity[str(old["id"])] = key
        room = {
            k: deepcopy(old[k])
            for k in ("name", "capacity", "area", "amenities")
            if k in old
        }
        room.update(client_key=key, beds=[])
        for bed in old.get("beds", []):
            bed_key = str(uuid.uuid4())
            identity[str(bed["id"])] = bed_key
            room["beds"].append({"client_key": bed_key, "name": bed["name"]})
        rooms.append(room)
    offers = []
    for old in raw.get("offers", []):
        if old.get("archived"):
            continue
        offers.append(
            {
                "client_key": str(uuid.uuid4()),
                "name": old.get("name", ""),
                "rental_scope": old["rental_scope"],
                "terms": deepcopy(old.get("terms", {})),
                "room_ids": [identity[str(v)] for v in old.get("room_ids", [])],
                **(
                    {"bed_id": identity[str(old["bed_id"])]}
                    if old.get("bed_id")
                    else {}
                ),
                "availability": "unavailable",
                "inherited_fields": [],
            }
        )
    return normalize_inventory(
        {
            "schema_version": 1,
            "mode": raw["mode"],
            "expected_revision": 0,
            "rooms": rooms,
            "offers": offers,
            "shared_defaults": {},
        }
    )


TEMPLATE_FIELDS = (
    "title",
    "description",
    "price",
    "price_period",
    "property_type",
    "is_furnished",
    "bedrooms",
    "bathrooms",
    "area",
    "space",
    "rental_period",
    "suitable_for",
    "smoking_allowed",
    "governorate",
    "city",
    "district",
    "street",
    "country",
    "latitude",
    "longitude",
    "deposit",
    "has_wifi",
    "has_elevator",
    "has_garage",
    "has_security",
    "has_balcony",
    "has_air_conditioning",
    "near_metro",
    "has_natural_gas",
    "has_electricity_meter",
    "has_water_meter",
)


@transaction.atomic
def create_batch_item(user, data, row):
    User.objects.select_for_update().get(pk=user.pk)
    digest = fingerprint(
        {
            "template_id": str(data["template_id"]),
            "parent_kind": data.get("parent_kind"),
            "parent_id": str(data.get("parent_id", "")),
            "unit": row,
        }
    )
    previous = PortfolioBatchItem.objects.filter(
        owner=user, batch_key=data["batch_key"], item_key=row["item_key"]
    ).first()
    if previous:
        if previous.fingerprint != digest:
            raise RentalConflict(
                "This unit submission was already used with different values.",
                code="idempotency_conflict",
            )
        return previous.property
    parent = None
    if data.get("parent_id"):
        parent = parent_for(user, data["parent_kind"], data["parent_id"], lock=True)
        assert_topology_mutable(parent)
    source = get_object_or_404(
        Property, id=data["template_id"], owner=user, retired_at=None
    )
    values = {k: getattr(source, k) for k in TEMPLATE_FIELDS}
    values.update(
        {
            k: row[k]
            for k in (
                "title",
                "bedrooms",
                "bathrooms",
                "area",
                "floor",
                "is_furnished",
                "occupancy_capacity",
            )
            if k in row
        }
    )
    values.update(unit_code=row["unit_code"], rental_inventory=cloned_inventory(source))
    if parent:
        values[data["parent_kind"]] = parent
    prop = PropertyService.create_property(user, values)
    PortfolioBatchItem.objects.create(
        owner=user,
        batch_key=data["batch_key"],
        item_key=row["item_key"],
        fingerprint=digest,
        property=prop,
    )
    if parent:
        parent.topology_revision += 1
        parent.revision += 1
        parent.save()
    audit(
        prop,
        user,
        "portfolio_unit_created",
        metadata={
            "batch_key": str(data["batch_key"]),
            "item_key": str(row["item_key"]),
            "template_id": str(source.id),
            "media_copied": False,
        },
    )
    return prop


def create_batch(user, data):
    results = []
    for row in data["units"]:
        try:
            prop = create_batch_item(user, data, row)
            results.append(
                {
                    "item_key": str(row["item_key"]),
                    "status": "created",
                    "property_id": str(prop.id),
                    "unit_code": prop.unit_code,
                }
            )
        except (ValidationError, RentalConflict, IntegrityError) as error:
            code = error.get_codes() if hasattr(error, "get_codes") else "invalid_unit"
            results.append(
                {
                    "item_key": str(row["item_key"]),
                    "status": "failed",
                    "code": code if isinstance(code, str) else "invalid_unit",
                    "message": "Review this unit's values and code before retrying.",
                }
            )
    return {
        "batch_key": str(data["batch_key"]),
        "complete": all(r["status"] == "created" for r in results),
        "results": results,
    }


@transaction.atomic
def submit_batch(user, data):
    import json
    from core_apps.properties.models import PortfolioBatch

    User.objects.select_for_update().get(pk=user.pk)
    batch, created = PortfolioBatch.objects.select_for_update().get_or_create(
        id=data["batch_key"], defaults={"owner": user}
    )
    if batch.owner_id != user.pk:
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("This batch belongs to another account.")
    if created and data["expected_revision"] != 0:
        raise RentalConflict(
            "A new batch starts at revision zero.", code="stale_revision"
        )
    if not created:
        require_revision(batch, data["expected_revision"])
        for key in ("template_id", "parent_kind", "parent_id"):
            if str(batch.draft.get(key, "")) != str(data.get(key, "")):
                raise RentalConflict(
                    "A submitted batch keeps its original template and parent.",
                    code="batch_scope_changed",
                )
        batch.revision += 1
    # Successful entries cannot be rewritten by a retry. Reject before making
    # new writes, retaining both the canonical IDs and their acknowledged input.
    successful = {
        row["item_key"] for row in batch.results if row["status"] == "created"
    }
    originals = {row["item_key"]: row for row in batch.draft.get("units", [])}
    normalized = json.loads(json.dumps(data["units"], default=str))
    if any(
        row["item_key"] in successful and row != originals[row["item_key"]]
        for row in normalized
    ):
        raise RentalConflict(
            "A completed batch unit must be edited through its property record.",
            code="idempotency_conflict",
        )
    result = create_batch(user, data)
    results = {row["item_key"]: row for row in batch.results}
    results.update({row["item_key"]: row for row in result["results"]})
    batch.results = list(results.values())
    batch.complete = all(row["status"] == "created" for row in batch.results)
    draft = json.loads(
        json.dumps(
            {
                k: v
                for k, v in data.items()
                if k not in {"request_key", "expected_revision"}
            },
            default=str,
        )
    )
    units = {row["item_key"]: row for row in batch.draft.get("units", [])}
    units.update({row["item_key"]: row for row in draft["units"]})
    batch.draft = {**draft, "units": list(units.values())}
    batch.save()
    audit(batch, user, "portfolio_batch_submitted")
    return batch


def batch_payload(batch, language=None):
    from core_apps.common.translation import translate_message

    return {
        "id": str(batch.id),
        "revision": batch.revision,
        "batch_key": str(batch.id),
        "complete": batch.complete,
        "results": [
            {
                **row,
                **(
                    {"message": translate_message(row["message"], language)}
                    if row.get("message")
                    else {}
                ),
            }
            for row in batch.results
        ],
        "draft": batch.draft,
    }


def unit_payload(prop):
    from .portfolio_changes import unit_version, defaults_for

    return {
        "id": str(prop.id),
        "code": prop.unit_code,
        "title": prop.title,
        "floor": prop.floor,
        "capacity": prop.occupancy_capacity,
        "status": prop.status,
        "building_id": str(prop.building.id) if prop.building_id else None,
        "complex_id": str(prop.complex.id) if prop.complex_id else None,
        "bedrooms": prop.bedrooms,
        "bathrooms": prop.bathrooms,
        "area": prop.area,
        "is_furnished": prop.is_furnished,
        "inventory_revision": (prop.rental_inventory or {}).get("revision", 0),
        "version": unit_version(prop),
        "inheritance": prop.portfolio_inheritance,
        "available_defaults": defaults_for(prop),
        "retired": prop.retired_at is not None,
    }


def container_payload(item):
    from .portfolio_changes import FACT_FIELDS, json_value

    building = isinstance(item, ResidentialBuilding)
    units = list(
        units_for(item)
        .select_related("building", "complex")
        .order_by("floor", "unit_code", "id")
    )
    return {
        "id": str(item.id),
        "kind": "building" if building else "complex",
        "name": item.name,
        "code": item.code,
        "address": item.address,
        "description": item.description,
        "facilities": item.facilities,
        "facts": json_value({f: getattr(item, f) for f in FACT_FIELDS}),
        "complex_id": str(item.complex.id) if building and item.complex_id else None,
        "floors": item.floors if building else None,
        "revision": item.revision,
        "topology_revision": item.topology_revision,
        "authority_status": item.authority_status,
        "registered_units": len(units),
        "declared_units": item.declared_units if building else None,
        "declared_buildings": None if building else item.declared_buildings,
        "declared_standalone_units": (
            None if building else item.declared_standalone_units
        ),
        "capacity": (
            sum(p.occupancy_capacity for p in units)
            if units and all(p.occupancy_capacity is not None for p in units)
            else None
        ),
        "units": [unit_payload(p) for p in units],
        "buildings": (
            []
            if building
            else [
                {
                    "id": str(b.id),
                    "name": b.name,
                    "code": b.code,
                    "registered_units": b.units.filter(retired_at=None).count(),
                    "declared_units": b.declared_units,
                }
                for b in item.buildings.order_by("code")
            ]
        ),
    }
