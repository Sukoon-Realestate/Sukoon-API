"""Owner facts/defaults and version-bound bulk edits of canonical units."""

from copy import deepcopy
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.properties.models import (
    Property,
    PortfolioChangeSet,
    ResidentialBuilding,
)
from core_apps.properties.services.property import PropertyService
from ...portfolio_fields import AssetFacts
from ..rental_lifecycle.common import audit, require_revision
from ..rental_phase2 import RentalConflict
from .portfolio import parent_for, units_for, assert_topology_mutable

FACT_FIELDS = tuple(AssetFacts().fields)
LIVE_LEASES = [
    "draft",
    "pending",
    "pending_signatures",
    "signed",
    "active",
    "termination_pending",
]


def json_value(value):
    import json

    return json.loads(json.dumps(value, default=str))


def unit_version(prop):
    return prop.updated_at.isoformat()


def assert_unit_mutable(prop):
    if prop.retired_at:
        raise RentalConflict(
            "This inventory identity has been retired.", code="inventory_retired"
        )
    if (
        prop.rental_day_locks.exists()
        or prop.digital_leases.filter(status__in=LIVE_LEASES).exists()
    ):
        raise RentalConflict(
            "An existing commitment requires a supported amendment before this change.",
            code="inventory_conflict",
        )
    if prop.building_id:
        assert_topology_mutable(prop.building)
    elif prop.complex_id:
        assert_topology_mutable(prop.complex)


def mark_overrides(prop, fields):
    """Called by ordinary unit edits too, so bulk inheritance cannot undo them."""
    metadata = deepcopy(prop.portfolio_inheritance)
    from ...portfolio_fields import UnitDefaults

    for field in set(fields) & set(UnitDefaults().fields):
        metadata[field] = {"mode": "override"}
    prop.portfolio_inheritance = metadata


def defaults_for(prop):
    parents = []
    if prop.building_id:
        if prop.building.complex_id:
            parents.append(prop.building.complex)
        parents.append(prop.building)
    elif prop.complex_id:
        parents.append(prop.complex)
    result = {}
    for parent in parents:
        for field, value in parent.unit_defaults.items():
            result[field] = {
                "value": value,
                "source_id": str(parent.id),
                "source_name": parent.name,
                "source_revision": parent.revision,
                "mode": "inherited",
            }
    return result


@transaction.atomic
def update_container(user, kind, identity, data):
    parent = parent_for(user, kind, identity, lock=True)
    require_revision(parent, data["expected_revision"])
    if data["kind"] != kind or (
        kind == "building"
        and str(data.get("complex_id", ""))
        != (str(parent.complex.id) if parent.complex_id else "")
    ):
        raise RentalConflict(
            "Use an inventory change to move an existing asset.",
            code="reparenting_required",
        )
    structure = (
        ("declared_units", "floors")
        if kind == "building"
        else ("declared_buildings", "declared_standalone_units")
    )
    changed_structure = any(
        getattr(parent, f) != data.get(f) for f in structure if f in data
    )
    if changed_structure:
        assert_topology_mutable(parent)
        if kind == "building" and data["declared_units"] < units_for(parent).count():
            raise RentalConflict(
                "The declared count cannot be smaller than registered inventory.",
                code="inventory_incomplete",
            )
        if kind == "complex" and (
            data["declared_buildings"] < parent.buildings.filter(archived=False).count()
            or data["declared_standalone_units"]
            < parent.standalone_units.filter(retired_at=None).count()
        ):
            raise RentalConflict(
                "The declared count cannot be smaller than registered inventory.",
                code="inventory_incomplete",
            )
    fields = ("name", "code", "address", "description", "facilities", *structure)
    commercial_changed = changed_structure or any(
        getattr(parent, f) != data.get(f, getattr(parent, f)) for f in fields
    )
    commercial_changed |= any(
        getattr(parent, f) != value
        for f, value in data.get("facts", {}).items()
        if f not in {"private_access", "contact_name", "contact_phone", "unit_defaults"}
    )
    authority_changed = changed_structure or any(
        getattr(parent, f) != data.get(f, getattr(parent, f))
        for f in ("name", "code", "address")
    )
    if authority_changed:
        assert_topology_mutable(parent)
        parent.authority_status = "pending"
        parent.authority_reviewed_by = None
        parent.authority_reference = ""
    for field in fields:
        if field in data:
            setattr(parent, field, data[field])
    for field, value in data.get("facts", {}).items():
        setattr(parent, field, value)
    parent.revision += 1
    if commercial_changed:
        parent.commercial_revision += 1
    if changed_structure:
        parent.topology_revision += 1
    parent.save()
    audit(
        parent,
        user,
        "portfolio_asset_updated",
        metadata={
            "authority_reset": authority_changed,
            "unit_defaults_propagated": False,
        },
    )
    return parent


def change_payload(change):
    return {
        "id": str(change.id),
        "revision": change.revision,
        "operation": change.operation,
        "preview": change.preview,
        "results": change.results,
        "applied": change.applied_at is not None,
    }


def change_for(user, identity, lock=False):
    qs = (
        PortfolioChangeSet.objects.select_for_update()
        if lock
        else PortfolioChangeSet.objects
    )
    return get_object_or_404(qs, id=identity, owner=user)


def _bulk_row(prop, version, data):
    row = {
        "id": str(prop.id),
        "code": prop.unit_code,
        "version": version,
        "changes": {},
        "inheritance": {},
        "status": "ready",
        "skipped_fields": [],
    }
    if version != unit_version(prop):
        row.update(status="blocked", code_reason="stale_revision")
        return row
    try:
        assert_unit_mutable(prop)
    except RentalConflict as error:
        row.update(status="blocked", code_reason=error.get_codes())
        return row
    for field, value in data["changes"].items():
        row["changes"][field] = {
            "before": getattr(prop, field),
            "after": value,
            "source": "override",
        }
        row["inheritance"][field] = {"mode": "override"}
    defaults = defaults_for(prop)
    for field in data["inherit_fields"]:
        origin = prop.portfolio_inheritance.get(field, {"mode": "override"})
        if field not in defaults or (
            origin["mode"] == "override" and not data["reset_overrides"]
        ):
            row["skipped_fields"].append(field)
            continue
        inherited = defaults[field]
        row["changes"][field] = {
            "before": getattr(prop, field),
            "after": inherited["value"],
            "source": inherited["source_name"],
        }
        row["inheritance"][field] = inherited
    if not row["changes"]:
        row["status"] = "unchanged"
    return json_value(row)


@transaction.atomic
def preview_bulk(user, kind, identity, data):
    parent = parent_for(user, kind, identity, lock=True)
    require_revision(parent, data["expected_revision"])
    requested = {str(row["id"]): row["version"] for row in data["units"]}
    props = list(
        units_for(parent)
        .filter(id__in=requested)
        .select_related("building__complex", "complex")
        .order_by("pk")
    )
    if len(props) != len(requested) or any(prop.owner_id != user.pk for prop in props):
        raise PermissionDenied("Choose exact units you own inside this asset.")
    change = PortfolioChangeSet.objects.create(
        owner=user,
        **{kind: parent},
        operation="bulk_edit",
        preview={
            "parent_id": str(parent.id),
            "parent_kind": kind,
            "parent_revision": parent.revision,
            "reason": data["reason"],
            "rows": [_bulk_row(p, requested[str(p.id)], data) for p in props],
        }
    )
    audit(change, user, "portfolio_bulk_previewed", data["reason"])
    return change


@transaction.atomic
def apply_bulk(user, identity, data):
    change = change_for(user, identity, lock=True)
    require_revision(change, data["expected_revision"])
    if change.applied_at or change.operation != "bulk_edit":
        raise RentalConflict(
            "Create a new preview for unresolved changes.",
            code="change_already_applied",
        )
    parent = parent_for(
        user, change.preview["parent_kind"], change.preview["parent_id"], lock=True
    )
    parent_stale = parent.revision != change.preview["parent_revision"]
    # A complex edit serializes with child edits, which always lock this root.
    results = []
    for row in change.preview["rows"]:
        result = {"id": row["id"], "code": row["code"], "status": row["status"]}
        if row["status"] != "ready":
            result.update(code_reason=row.get("code_reason", "no_changes"))
        else:
            try:
                with transaction.atomic():
                    prop = get_object_or_404(
                        Property.objects.select_for_update(), id=row["id"], owner=user
                    )
                    if (
                        parent_stale
                        or unit_version(prop) != row["version"]
                        or not units_for(parent).filter(pk=prop.pk).exists()
                    ):
                        raise RentalConflict(
                            "Review current values before editing.",
                            code="stale_revision",
                        )
                    assert_unit_mutable(prop)
                    current_defaults = defaults_for(prop)
                    if any(
                        meta.get("mode") == "inherited"
                        and current_defaults.get(field) != meta
                        for field, meta in row["inheritance"].items()
                    ):
                        raise RentalConflict(
                            "Parent defaults changed. Create a fresh preview.",
                            code="stale_revision",
                        )
                    prop = PropertyService.update_property(
                        prop, {key: v["after"] for key, v in row["changes"].items()}
                    )
                    prop.portfolio_inheritance.update(row["inheritance"])
                    prop.save(update_fields=["portfolio_inheritance", "updated_at"])
                    result.update(status="updated", version=unit_version(prop))
                    audit(
                        prop,
                        user,
                        "portfolio_bulk_unit_updated",
                        change.preview["reason"],
                        {"change_id": str(change.id), "fields": list(row["changes"])},
                    )
            except RentalConflict as error:
                result.update(status="failed", code_reason=error.get_codes())
        results.append(result)
    change.results = results
    change.applied_at = timezone.now()
    change.revision += 1
    change.save()
    audit(change, user, "portfolio_bulk_applied", metadata={"results": results})
    return change
