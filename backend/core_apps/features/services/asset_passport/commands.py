from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ...asset_passport_models import (
    AssetItem,
    AssetLocationPeriod,
    AssetLifecycleEvent,
    AssetObservation,
)
from ..planning import civil_date, text_field
from ..rental_lifecycle.common import audit
from ..rental_phase2 import RentalConflict
from .access import property_for
from . import evidence


def effective_date(data):
    value = civil_date(data.get("effective_on"), "effective_on")
    if value > timezone.localdate():
        raise ValidationError(
            {"effective_on": "Record an observed lifecycle date, not a future move."}
        )
    return value


def location_fields(prop, data):
    room_id = text_field(data, "room_id", limit=90)
    if room_id and room_id not in {
        str(row.get("id")) for row in (prop.rental_inventory or {}).get("rooms", [])
    }:
        raise ValidationError(
            {"room_id": "Choose a room in the canonical property inventory."}
        )
    return {
        "room_id": room_id,
        "space_label": text_field(data, "space_label", limit=120),
    }


def register(user, prop, data, predecessor=None):
    when = effective_date(data)
    item = AssetItem.objects.create(
        property=prop,
        registered_by=user,
        label=text_field(data, "label", required=True, limit=200),
        category=text_field(data, "category", required=True, limit=80),
        make_model=text_field(data, "make_model", limit=160),
        serial_number=text_field(data, "serial_number", limit=120),
        predecessor=predecessor,
    )
    AssetLocationPeriod.objects.create(
        asset=item, property=prop, starts_on=when, **location_fields(prop, data)
    )
    AssetLifecycleEvent.objects.create(
        asset=item,
        actor=user,
        action="registered",
        effective_on=when,
        to_property=prop,
        related_asset=predecessor,
    )
    audit(item, user, "asset_registered")
    return item


def lifecycle(user, asset, action, data):
    if asset.status in {"replaced", "retired"}:
        raise RentalConflict("This physical identity is closed.", code="asset_closed")
    when = effective_date(data)
    period = asset.locations.select_for_update().get(ends_on_exclusive=None)
    if (
        when < period.starts_on
        or asset.observations.filter(observed_on__gte=when).exists()
    ):
        raise ValidationError(
            {
                "effective_on": "The date must preserve the recorded location and observations. Choose a later date."
            }
        )
    previous = asset.property
    destination, successor = None, None
    if action == "move":
        destination = property_for(user, data.get("property_id"), write=True, lock=True)
        fields = location_fields(destination, data)
    elif action == "replace":
        successor = register(user, previous, data, predecessor=asset)
        asset.status = "replaced"
    elif action == "retire":
        asset.status = "retired"
    else:
        raise ValidationError(
            {"action": "Choose a supported physical lifecycle action."}
        )
    period.ends_on_exclusive = when
    period.save(update_fields=["ends_on_exclusive", "updated_at"])
    if destination:
        AssetLocationPeriod.objects.create(
            asset=asset, property=destination, starts_on=when, **fields
        )
        asset.property = destination
    asset.revision += 1
    asset.save()
    AssetLifecycleEvent.objects.create(
        asset=asset,
        actor=user,
        action=action,
        effective_on=when,
        from_property=previous,
        to_property=destination,
        related_asset=successor,
    )
    audit(asset, user, "asset_" + action)
    return asset


def observe(user, asset, data):
    if asset.status in {"retired", "replaced"}:
        raise RentalConflict(
            "This item is closed. Use its successor for current observations.",
            code="asset_closed",
        )
    when = civil_date(data.get("observed_on"), "observed_on")
    if when > timezone.localdate():
        raise ValidationError(
            {"observed_on": "An observation cannot describe a future date."}
        )
    condition = data.get("condition")
    if condition not in {"not_inspected", "unknown", "good", "worn", "damaged"}:
        raise ValidationError({"condition": "Select an explicit observed condition."})
    source, media = evidence.validate(user, asset, data, when)
    from .analysis import capture_context

    row = AssetObservation.objects.create(
        asset=asset,
        property=source.lease.property,
        lease=source.lease,
        author=user,
        observed_on=when,
        condition=condition,
        note=text_field(data, "note", limit=2000),
        source_kind=data["source_kind"],
        source_id=source.id,
        source_revision=source.revision,
        source_status=source.status,
        capture_context=capture_context(data),
    )
    row.evidence.set(media)
    asset.revision += 1
    asset.save(update_fields=["revision", "updated_at"])
    audit(asset, user, "asset_observed", metadata={"observation_id": str(row.id)})
    return asset


def update(user, asset, data):
    """An owner's explicit record correction never changes physical identity or stock."""
    if asset.status in {"retired", "replaced"}:
        raise RentalConflict("This physical identity is closed.", code="asset_closed")
    when = effective_date(data)
    status = data.get("status", asset.status)
    if status not in {
        "proposed",
        "active",
        "under_maintenance",
        "temporarily_unavailable",
    }:
        raise ValidationError({"status": "Choose a supported recorded item status."})
    latest = asset.events.order_by("-effective_on").first()
    if latest and when < latest.effective_on:
        raise ValidationError(
            {
                "effective_on": "A status correction must follow the recorded lifecycle history."
            }
        )
    previous = {
        key: getattr(asset, key)
        for key in ("status", "label", "category", "make_model", "serial_number")
    }
    for key, limit in (
        ("label", 200),
        ("category", 80),
        ("make_model", 160),
        ("serial_number", 120),
    ):
        setattr(
            asset,
            key,
            text_field(data, key, required=key in {"label", "category"}, limit=limit),
        )
    asset.status = status
    asset.revision += 1
    asset.save()
    AssetLifecycleEvent.objects.create(
        asset=asset,
        actor=user,
        action="status_" + status,
        effective_on=when,
        from_property=asset.property,
        to_property=asset.property,
    )
    audit(
        asset,
        user,
        "asset_record_updated",
        metadata={
            "previous_record": previous,
            "physical_identity_unchanged": True,
            "inventory_changed": False,
        },
    )
    return asset
