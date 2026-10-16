from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from ..models import PropertyDecisionFact, RentalVerificationClaim
from ..rental_lifecycle_serializers import SelectionBody, ConfirmationBody, FactBody
from ..services.rental_lifecycle.access import property_for
from ..services.rental_lifecycle.decisions import decision_summary, FACT_CODES
from ..services.rental_lifecycle.reservations import confirm_availability
from ..services.rental_lifecycle.claims import claim_current
from ..services.rental_lifecycle.common import audit, require_revision
from ..services.rental_phase2 import RentalConflict
from .common import endpoint, validated, mutate


@endpoint(["GET"])
def property_decision(request, property_id):
    data = validated(SelectionBody, request.query_params.dict())
    return Response(
        decision_summary(property_for(request.user, property_id), data, request.user)
    )


@endpoint(["POST"])
def availability_confirmation(request, property_id):
    data = validated(ConfirmationBody, request.data)

    def execute(prop):
        item = confirm_availability(prop, request.user, data)
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

    return mutate(
        request,
        f"availability.confirm.{property_id}",
        lambda: property_for(request.user, property_id, owner=True, lock=True),
        execute,
    )


@endpoint(["POST"])
def property_fact(request, property_id):
    data = validated(FactBody, request.data)

    def execute(prop):
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
            request.user,
            timezone.now(),
            data.get("expires_at"),
        )
        item.save()
        audit(item, request.user, "property_fact.recorded")
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

    return mutate(
        request,
        f"property_fact.save.{property_id}",
        lambda: property_for(request.user, property_id, owner=True, lock=True),
        execute,
    )
