"""Advertising adapter: the shared invoice owns collection; the ad owns delivery."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from core_apps.advertising.models import Advertisement, AdvertisingPlan
from core_apps.advertising.services import (
    destination_is_eligible,
    media_is_available,
    activate_with_mock_payment,
    AdvertisingServiceError,
)
from .rental_phase2 import RentalConflict


def advertising_snapshot(user, body):
    if body["workspace"] != "owner":
        raise ValidationError("Advertisements are purchased in the owner workspace.")
    ad = get_object_or_404(
        Advertisement.objects.select_for_update(of=("self",)),
        id=body.get("advertisement_id"),
        owner=user,
    )
    if ad.status != "pending_payment":
        raise RentalConflict(
            "This advertisement is not awaiting payment.", code="invalid_transition"
        )
    validate_advertisement(ad)
    plan = ad.plan_snapshot
    price = plan.get("price") or {
        "amount_minor": plan.get("amount_minor"),
        "currency": plan.get("currency", "EGP"),
        "exponent": plan.get("exponent", 2),
    }
    if (
        price.get("currency") != "EGP"
        or price.get("exponent") != 2
        or not isinstance(price.get("amount_minor"), int)
        or price.get("amount_minor", 0) <= 0
    ):
        raise ValidationError("The advertisement price is invalid.")
    return {
        "subject_id": str(ad.id),
        "name_en": ad.title,
        "name_ar": ad.title,
        "advertising_plan": plan,
        **price,
    }


def validate_advertisement(ad):
    if not AdvertisingPlan.objects.filter(
        id=ad.plan_snapshot["id"], active=True
    ).exists():
        raise RentalConflict(
            "The selected plan is unavailable.", code="plan_unavailable"
        )
    if not destination_is_eligible(ad) or not media_is_available(ad):
        raise RentalConflict(
            "The advertisement destination or media is unavailable.",
            code="advertisement_unavailable",
        )


def activate_advertising_invoice(invoice, attempt):
    ad = get_object_or_404(
        Advertisement.objects.select_for_update(of=("self",)).select_related(
            "operation"
        ),
        id=invoice.purchase_snapshot["subject_id"],
        owner=attempt.payer,
    )
    validate_advertisement(ad)
    try:
        activate_with_mock_payment(
            attempt.payer,
            ad.id,
            f"{ad.operation.operation_id}-payment",
            "mock",
            invoice=invoice,
            attempt=attempt,
        )
    except AdvertisingServiceError as error:
        raise RentalConflict(error.message, code="advertisement_unavailable") from error
