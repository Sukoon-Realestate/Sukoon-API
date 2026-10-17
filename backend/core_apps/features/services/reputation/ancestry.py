"""Freeze original unit ancestry; never fill historical gaps with today's parent."""

from django.utils import timezone
from core_apps.properties.models import Property


def from_property(prop):
    prop = Property.objects.select_related("building__complex", "complex").get(
        pk=prop.pk
    )
    building = prop.building if prop.building_id else None
    complex_ = (
        building.complex
        if building and building.complex_id
        else prop.complex if prop.complex_id else None
    )
    return {
        "property_id": str(prop.id),
        "building_id": str(building.id) if building else None,
        "complex_id": str(complex_.id) if complex_ else None,
        "building_name": building.name if building else "",
        "complex_name": complex_.name if complex_ else "",
        "captured_at": timezone.now().isoformat(),
        "basis": "confirmed_occupancy",
    }


def from_snapshot(snapshot, prop):
    snapshot = snapshot or {}
    for unit in snapshot.get("units", []):
        if str(unit.get("id")) == str(prop.id):
            return {
                k: unit.get(k)
                for k in ("building_id", "complex_id", "building_name", "complex_name")
            } | {"property_id": str(prop.id), "basis": "contract_inventory_snapshot"}
    value = snapshot.get("reputation_ancestry", snapshot)
    if "building_id" in value or "complex_id" in value:
        return {
            k: value.get(k)
            for k in ("building_id", "complex_id", "building_name", "complex_name")
        } | {"property_id": str(prop.id), "basis": "contract_inventory_snapshot"}
    return {"property_id": str(prop.id), "basis": "historical_ancestry_unavailable"}


def freeze_handover(handover):
    if handover.context_snapshot:
        return handover.context_snapshot
    ancestry = (
        from_property(handover.lease.property)
        if handover.possession_on >= timezone.localdate()
        else from_snapshot(handover.lease.offer_snapshot, handover.lease.property)
    )
    return {
        **ancestry,
        "owner_id": str(handover.lease.owner.id),
        "tenant_id": str(handover.lease.tenant.id),
    }


def for_stay(start):
    return start.context_snapshot or from_snapshot(
        start.lease.offer_snapshot, start.lease.property
    )
