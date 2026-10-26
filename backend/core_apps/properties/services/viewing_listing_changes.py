"""Propagate material listing edits to open viewings of the exact accommodation."""

from copy import deepcopy
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.utils import timezone
from ..models import PropertyVisit


def _money(value):
    if value is None:
        return None
    try:
        return format(Decimal(str(value)).normalize(), "f")
    except InvalidOperation:
        return str(value)


def source_state(prop, offer_id):
    from core_apps.features.services.tenancy_invitations_parts.validate_accounts import (
        _room_details,
    )

    inventory = prop.rental_inventory or {}
    offer = next(
        (row for row in inventory.get("offers", []) if str(row.get("id")) == offer_id),
        None,
    )
    terms = (offer or {}).get("terms", {})
    rooms = _room_details(inventory, offer) if offer else {}
    selected_rooms = [
        room
        for room in inventory.get("rooms", [])
        if (offer or {}).get("rental_scope") == "entire_property"
        or str(room.get("id")) in rooms.get("room_ids", [])
    ]
    return {
        # Stable catalog identity: a translated label change is not relocation.
        "location": {
            "governorate": prop.governorate_id,
            "city": prop.city_id,
            "district": prop.district_catalog_id or prop.district,
            "street": prop.street,
            "latitude": _money(prop.latitude),
            "longitude": _money(prop.longitude),
        },
        "accommodation": {
            "floor": prop.floor,
            "building_id": prop.building_id,
            "complex_id": prop.complex_id,
            "scope": (offer or {}).get("rental_scope", "entire_property"),
            "rooms": sorted(rooms.get("room_ids", [])),
            "bed": rooms.get("bed_id"),
            "physical_units": sorted(
                (
                    str(room["id"]),
                    sorted(
                        str(bed["id"])
                        for bed in room.get("beds", [])
                        if (offer or {}).get("rental_scope") != "bed"
                        or str(bed["id"]) == rooms.get("bed_id")
                    ),
                )
                for room in selected_rooms
            ),
        },
        "availability": not offer_id
        or bool(
            offer
            and not offer.get("archived")
            and offer.get("availability") == "available"
        ),
        "capacity": (
            rooms.get("capacity")
            if rooms.get("capacity") is not None
            else prop.occupancy_capacity
        ),
        "price": _money(terms.get("price") if offer_id else prop.price),
        "price_period": terms.get("price_period") if offer_id else prop.price_period,
        "deposit": _money(terms.get("deposit")),
        "rental_period": terms.get("rental_period", prop.rental_period),
        "suitable_for": terms.get("suitable_for", prop.suitable_for),
        "smoking_allowed": terms.get("smoking_allowed", prop.smoking_allowed),
        "rules": deepcopy(terms.get("rules")),
        "services": deepcopy(terms.get("included_services")),
    }


def snapshot(prop):
    """Captured before mutation, while PropertyService owns the property lock."""
    ids = set(
        prop.visits.filter(status__in=["pending", "confirmed"]).values_list(
            "offer_id", flat=True
        )
    )
    return {identity: source_state(prop, identity) for identity in ids}


def impact_reason(current, fields, occupants):
    if not current["availability"]:
        return "source_unavailable"
    if "accommodation" in fields:
        return "accommodation_changed"
    if "location" in fields:
        return "location_changed"
    if current["capacity"] is not None and current["capacity"] < occupants:
        return "capacity_exceeded"
    return "terms_changed"


@transaction.atomic
def propagate(prop, before):
    from core_apps.features.planning_models import GroupProcess
    from core_apps.features.planning_group_views_parts.process_payload import (
        invalidate_process,
    )
    from .viewing_commands import notify

    differences = {}
    for offer_id, old in before.items():
        current = source_state(prop, offer_id)
        changes = [
            {"field": key, "before": old[key], "after": current[key]}
            for key in old
            if old[key] != current[key]
        ]
        if changes:
            differences[offer_id] = (current, changes)
    if not differences:
        return
    candidates = (
        PropertyVisit.objects.filter(
            property=prop, status__in=["pending", "confirmed"], offer_id__in=differences
        )
        .exclude(participant_decisions__isnull=False)
        .exclude(rental_invitations__isnull=False)
    )

    # Same process -> viewing order as membership/consent invalidation. The
    # caller already locks the property, preventing a new appointment race.
    processes = {
        process.visit_id: process
        for process in GroupProcess.objects.select_for_update()
        .filter(property=prop, visit__in=candidates)
        .order_by("pk")
    }
    visits = candidates.select_for_update().order_by("pk")
    for visit in visits:
        # A decision may have committed while this SELECT waited for the row.
        # Recheck related records after the lock rather than its earlier snapshot.
        if visit.participant_decisions.exists() or visit.rental_invitations.exists():
            continue
        current, changes = differences[visit.offer_id]
        fields = {row["field"] for row in changes}
        process = processes.get(visit.pk)
        occupants = max(
            (visit.stay_preferences or {}).get("occupants", 1),
            len(process.participant_ids) if process else 1,
        )
        reason = impact_reason(current, fields, occupants)
        previous = visit.status
        if reason != "terms_changed" and process:
            invalidate_process(process, reason_code="consent_or_source_changed")
            visit.refresh_from_db()
        visit.status = "canceled" if reason != "terms_changed" else visit.status
        visit.revision += 1
        visit.change_history = [
            *visit.change_history,
            {
                "at": timezone.now().isoformat(),
                "revision": visit.revision,
                "changed_fields": ["listing"],
                "from_status": previous,
                "to_status": visit.status,
                "reason_code": reason,
                "source_revision": prop.review_revision,
                "listing_changes": changes,
            },
        ]
        # This is a source event, not a rewrite of the immutable booked snapshot.
        # Ordinary save() owns appointment-field history; this locked update owns
        # only listing-impact history and its explicitly evaluated transition.
        PropertyVisit.objects.filter(pk=visit.pk).update(
            status=visit.status,
            revision=visit.revision,
            change_history=visit.change_history,
            updated_at=timezone.now(),
        )
        visit.property = prop
        notify(visit, "listing_changed")
