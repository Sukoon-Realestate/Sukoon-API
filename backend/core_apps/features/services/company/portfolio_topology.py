"""Previewed moves/splits/merges. Locks roots, buildings, then canonical units."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.properties.models import (
    Property,
    ResidentialBuilding,
    ResidentialComplex,
    PortfolioChangeSet,
)
from core_apps.properties.services.property import PropertyService
from ..rental_lifecycle.common import audit, require_revision
from ..rental_phase2 import RentalConflict
from .portfolio import parent_for, units_for, assert_topology_mutable, TEMPLATE_FIELDS
from .portfolio_changes import assert_unit_mutable, unit_version, json_value, change_for


def lock_parents(user, kind, identity, data):
    source = parent_for(user, kind, identity)
    target = (
        parent_for(user, data["target_kind"], data["target_id"])
        if data.get("target_id")
        else None
    )
    parents = [p for p in (source, target) if p is not None]
    complex_ids = {p.pk for p in parents if isinstance(p, ResidentialComplex)} | {
        p.complex_id
        for p in parents
        if isinstance(p, ResidentialBuilding) and p.complex_id
    }
    list(
        ResidentialComplex.objects.select_for_update()
        .filter(pk__in=complex_ids)
        .order_by("pk")
    )
    building_ids = {p.pk for p in parents if isinstance(p, ResidentialBuilding)}
    # A whole building move must also serialize with changes of its children.
    list(
        ResidentialBuilding.objects.select_for_update()
        .filter(pk__in=building_ids)
        .order_by("pk")
    )
    for parent in parents:
        old_root = (
            parent.complex_id if isinstance(parent, ResidentialBuilding) else None
        )
        parent.refresh_from_db()
        if isinstance(parent, ResidentialBuilding) and old_root != parent.complex_id:
            raise RentalConflict(
                "The parent changed. Create a fresh inventory preview.",
                code="stale_revision",
            )
    return source, target


def validate_scope(user, source, target, data, *, lock=False):
    if data["operation"] == "move_building":
        if not isinstance(source, ResidentialBuilding):
            raise RentalConflict("Select a building to move.", code="invalid_scope")
        if source.complex_id == target.pk:
            raise RentalConflict(
                "The building already belongs to this complex.", code="invalid_scope"
            )
        query = units_for(source)
    else:
        ids = [u["id"] for u in data["units"]]
        query = units_for(source).filter(id__in=ids)
        if query.count() != len(ids):
            raise PermissionDenied("Choose exact units in the source asset.")
    if lock:
        query = query.select_for_update(of=("self",))
    props = list(query.select_related("building__complex", "complex").order_by("pk"))
    if any(p.owner_id != user.pk for p in props):
        raise PermissionDenied(
            "Authority over a container does not grant ownership of its units."
        )
    if (
        data["operation"] in {"split_unit", "merge_units"}
        and len({(p.building_id, p.complex_id) for p in props}) != 1
    ):
        raise RentalConflict(
            "Merge units with the same direct parent.", code="invalid_scope"
        )
    if (
        target
        and data["operation"] == "move_units"
        and any(
            (
                p.building_id == target.pk
                if isinstance(target, ResidentialBuilding)
                else p.complex_id == target.pk
            )
            for p in props
        )
    ):
        raise RentalConflict(
            "The destination must be different from the current parent.",
            code="invalid_scope",
        )
    return props


def blockers(source, target, props, data):
    reasons = []
    try:
        assert_topology_mutable(source)
        if target:
            assert_topology_mutable(target)
        for prop in props:
            assert_unit_mutable(prop)
    except RentalConflict as error:
        reasons.append(error.get_codes())
    expected = {str(u["id"]): u["version"] for u in data["units"]}
    if any(unit_version(p) != expected.get(str(p.id), unit_version(p)) for p in props):
        reasons.append("stale_revision")
    return sorted(set(reasons))


@transaction.atomic
def preview_topology(user, kind, identity, data):
    source, target = lock_parents(user, kind, identity, data)
    require_revision(source, data["expected_revision"])
    if target:
        require_revision(target, data["target_revision"])
    props = validate_scope(user, source, target, data, lock=True)
    blocked = blockers(source, target, props, data)
    change = PortfolioChangeSet.objects.create(
        owner=user,
        **{kind: source},
        operation=data["operation"],
        preview=json_value(
            {
                "parent_kind": kind,
                "parent_id": str(source.id),
                "parent_revision": source.revision,
                "target_name": target.name if target else "",
                "data": data,
                "units": [
                    {
                        "id": str(p.id),
                        "code": p.unit_code,
                        "version": unit_version(p),
                        "building_id": p.building_id,
                        "complex_id": p.complex_id,
                    }
                    for p in props
                ],
                "blocked_reasons": blocked,
                "allowed": not blocked,
                "new_unit_count": len(data["replacements"]),
                "retains_original_identities": data["operation"].startswith("move_"),
            }
        )
    )
    audit(change, user, "portfolio_topology_previewed", data["reason"])
    return change


@transaction.atomic
def apply_topology(user, identity, data):
    change = change_for(user, identity, lock=True)
    require_revision(change, data["expected_revision"])
    if change.applied_at or not change.preview.get("allowed"):
        raise RentalConflict(
            "Create a fresh eligible preview before applying.",
            code="inventory_conflict",
        )
    preview = change.preview
    command = preview["data"]
    source, target = lock_parents(
        user, preview["parent_kind"], preview["parent_id"], command
    )
    require_revision(source, preview["parent_revision"])
    if target:
        require_revision(target, command["target_revision"])
    props = validate_scope(user, source, target, command, lock=True)
    expected = {p["id"]: p for p in preview["units"]}
    if {str(p.id) for p in props} != set(expected) or any(
        unit_version(p) != expected[str(p.id)]["version"] for p in props
    ):
        raise RentalConflict(
            "Inventory changed since the preview.", code="stale_revision"
        )
    blocked = blockers(source, target, props, command)
    if blocked:
        raise RentalConflict(
            "An inventory commitment or revision now prevents this change.",
            code=blocked[0],
        )
    changed_parents = {(source._meta.model_name, source.pk): source}
    if target:
        changed_parents[(target._meta.model_name, target.pk)] = target
    for p in props:
        for parent in (
            p.building if p.building_id else None,
            p.complex if p.complex_id else None,
        ):
            if parent:
                changed_parents[(parent._meta.model_name, parent.pk)] = parent
    results = []
    if change.operation == "move_building":
        if source.complex_id:
            old = source.complex
            changed_parents[(old._meta.model_name, old.pk)] = old
        source.complex = target
        source.save(update_fields=["complex", "updated_at"])
        results.append({"id": str(source.id), "status": "moved"})
    elif change.operation == "move_units":
        for prop in props:
            prop.building = target if isinstance(target, ResidentialBuilding) else None
            prop.complex = target if isinstance(target, ResidentialComplex) else None
            # Preserve physical facts, explicitly detach their old inheritance.
            prop.portfolio_inheritance = {
                k: {"mode": "override"} for k in prop.portfolio_inheritance
            }
            prop.status = Property.Status.UNDER_REVIEW
            prop.save()
            results.append({"id": str(prop.id), "status": "moved"})
    else:
        original = props[0]
        for prop in props:
            prop.retired_at = timezone.now()
            prop.status = Property.Status.HIDDEN
            prop.save(update_fields=["retired_at", "status", "updated_at"])
            results.append({"id": str(prop.id), "status": "retired"})
        for row in command["replacements"]:
            values = {k: getattr(original, k) for k in TEMPLATE_FIELDS}
            values.update(row)
            # A new physical layout requires new room/bed registration, media and
            # independent authority review. No bookings or verified state copy.
            values.update(
                building=original.building,
                complex=original.complex,
                rental_inventory={},
            )
            prop = PropertyService.create_property(user, values)
            prop.replaces.set(props)
            results.append(
                {"id": str(prop.id), "code": prop.unit_code, "status": "created"}
            )
    # Root complex revisions also protect stale whole-complex proposals.
    for parent in list(changed_parents.values()):
        if isinstance(parent, ResidentialBuilding) and parent.complex_id:
            root = parent.complex
            changed_parents.setdefault((root._meta.model_name, root.pk), root)
    for parent in changed_parents.values():
        parent.refresh_from_db()
        parent.revision += 1
        parent.topology_revision += 1
        parent.authority_status = "pending"
        parent.authority_reviewed_by = None
        parent.authority_reference = ""
        parent.save()
    change.results = results
    change.applied_at = timezone.now()
    change.revision += 1
    change.save()
    audit(
        change,
        user,
        "portfolio_topology_applied",
        command["reason"],
        {"results": results, "original_schedule_preserved": True},
    )
    return change
