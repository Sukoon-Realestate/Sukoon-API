"""Persist listing impact without rewriting an offer or its later commitments."""

from django.utils import timezone
from ..planning_models import HousingOffer, PlanningEvent
from .housing_request_reviews import LIVE
from core_apps.properties.services.viewing_listing_changes import source_state


def candidates(prop):
    return HousingOffer.objects.filter(
        property=prop,
        status__in=LIVE,
        tender_line__isnull=True,
        request__status__in=["published", "paused"],
    )


def source(prop):
    # Labels and unrelated conveniences do not invalidate an agreement.
    return {
        "offers": {
            str(row.selection.get("offer_id", "")): source_state(
                prop, str(row.selection.get("offer_id", ""))
            )
            for row in candidates(prop)
        },
        "property_type": prop.property_type_id,
        "furnished": prop.is_furnished,
        "amenities": {
            name: getattr(prop, field, False)
            for name, field in {
                "wifi": "has_wifi",
                "elevator": "has_elevator",
                "garage": "has_garage",
                "security": "has_security",
                "balcony": "has_balcony",
                "air_conditioning": "has_air_conditioning",
                "near_metro": "near_metro",
                "natural_gas": "has_natural_gas",
                "electricity_meter": "has_electricity_meter",
                "water_meter": "has_water_meter",
            }.items()
        },
    }


def record(item):
    from .student_housing.publication import participant_can_read

    recipients = [item.owner, item.request.user]
    if item.request.academic_plan_id:
        recipients += [
            row.user
            for row in item.request.academic_plan.participants.exclude(
                status="withdrawn"
            ).select_related("user")
            if participant_can_read(row.user, item.request)
        ]
    for recipient in {user.pk: user for user in recipients}.values():
        if not recipient.is_active:
            continue
        PlanningEvent.objects.get_or_create(
            recipient=recipient,
            event_key=f"housing_offer.source_changed:{item.id}:{item.revision}",
            defaults={
                "destination": {
                    "schema_version": "1",
                    "action_type": "open_housing_request",
                    "target_id": str(item.request.id),
                    "housing_offer_id": str(item.id),
                    "housing_section": "history",
                    "event_kind": "housing_offer_source_changed",
                    "revision": item.revision,
                    "workspace": (
                        "owner"
                        if recipient.pk == item.owner_id
                        else (
                            "student" if item.request.academic_plan_id else "individual"
                        )
                    ),
                }
            },
        )


def propagate(prop, before):
    after = source(prop)
    for item in (
        candidates(prop)
        .select_for_update(of=("self",))
        .select_related("request", "owner", "property")
        .order_by("pk")
    ):
        offer_id = str(item.selection.get("offer_id", ""))
        old, current = before["offers"].get(offer_id), after["offers"].get(offer_id)
        if old is None or current is None:
            continue
        changes = [
            {"field": key, "before": old[key], "after": current[key]}
            for key in old
            if old[key] != current[key]
        ]
        criteria = item.request.criteria
        for field in ("property_type", "furnished"):
            if (
                criteria.get(field) is not None
                and criteria.get(field) != ""
                and before[field] != after[field]
            ):
                changes.append(
                    {"field": field, "before": before[field], "after": after[field]}
                )
        for name in criteria.get("amenities", []):
            if before["amenities"].get(name) != after["amenities"].get(name):
                changes.append(
                    {
                        "field": f"amenity:{name}",
                        "before": before["amenities"].get(name),
                        "after": after["amenities"].get(name),
                    }
                )
        if not changes:
            continue
        item.revision += 1
        item.review_state = "incompatible"
        item.review_reasons = ["The selected accommodation or terms changed."]
        item.source_changes.append(
            {
                "at": timezone.now().isoformat(),
                "revision": item.revision,
                "source_revision": prop.review_revision,
                "listing_changes": changes,
            }
        )
        item.save(
            update_fields=[
                "revision",
                "review_state",
                "review_reasons",
                "source_changes",
                "updated_at",
            ]
        )
        record(item)
