"""Named decisions commands; adapters supply typed data and current actor."""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.features.models import PropertyDecisionFact, RentalVerificationClaim
from core_apps.features.services.rental_lifecycle.decisions import FACT_CODES
from core_apps.features.services.rental_lifecycle.reservations import (
    confirm_availability,
)
from core_apps.features.services.rental_lifecycle.claims import claim_current
from core_apps.features.services.rental_lifecycle.common import audit, require_revision
from core_apps.features.services.rental_phase2 import RentalConflict


def availability_confirmation_post_execute(prop, *, actor, data):
    item = confirm_availability(prop, actor, data)
    return (
        item,
        {
            "id": str(item.id),
            "revision": item.revision,
            "confirmed_at": item.confirmed_at.isoformat(),
            "inventory_revision": item.inventory_revision,
            "allowed_actions": [],
            "blocking_reasons": [],
        },
        200,
    )


def property_fact_post_execute(prop, *, actor, data):
    from core_apps.features.services.rental_lifecycle.decisions import STUDY_FACT_CODES

    if data["code"] in STUDY_FACT_CODES:
        from core_apps.features.services.planning import require_planning

        require_planning(actor, "student_study_facts")
    if data["code"] not in FACT_CODES:
        raise ValidationError({"code": "Unsupported decision fact."})
    if data["offer_id"] and data["offer_id"] not in {
        str(item["id"]) for item in (prop.rental_inventory or {}).get("offers", [])
    }:
        raise ValidationError(
            {"offer_id": "Select an offer belonging to this property."}
        )
    claim = None
    if data["classification"] == "verified":
        claim = get_object_or_404(
            RentalVerificationClaim,
            id=data.get("claim_id"),
            property=prop,
            subject_kind="property_fact",
            claim_code=data["code"],
        )
        if not claim_current(claim) or claim.public_wording != data["value"]:
            raise RentalConflict(
                "The exact fact has no current supporting review.",
                code="verification_required",
            )
    item = PropertyDecisionFact.objects.filter(
        property=prop, offer_id=data["offer_id"], code=data["code"]
    ).first()
    if item:
        require_revision(item, data["expected_revision"])
        item.revision += 1
    else:
        if data["expected_revision"] != 0:
            raise RentalConflict(
                "Review current decision facts.", code="stale_revision"
            )
        item = PropertyDecisionFact(
            property=prop, offer_id=data["offer_id"], code=data["code"]
        )
    item.value, item.classification, item.claim = (
        data["value"],
        data["classification"],
        claim,
    )
    item.recorded_by, item.checked_at, item.expires_at = (
        actor,
        timezone.now(),
        data.get("expires_at"),
    )
    item.save()
    audit(item, actor, "property_fact.recorded")
    return (
        item,
        {
            "id": str(item.id),
            "revision": item.revision,
            "code": item.code,
            "value": item.value,
            "classification": item.classification,
            "allowed_actions": [],
            "blocking_reasons": [],
        },
        200,
    )
