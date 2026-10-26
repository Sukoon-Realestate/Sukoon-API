"""Services: activate with mock payment."""

from django.db import transaction
from django.utils import timezone
from ..models import Advertisement, MockAdvertisementPayment
from .validate_banner import AdvertisingServiceError
from .ensure_media_persisted import (
    calendar_expiry,
    destination_is_eligible,
    media_is_available,
)


def activate_with_mock_payment(
    owner, advertisement_id, operation_id, payment_mode, *, invoice=None, attempt=None
):
    with transaction.atomic():
        advertisement = (
            Advertisement.objects.select_for_update()
            # Optional joins cannot be locked by PostgreSQL. Fetch the
            # destination separately; retain advertisement/owner/operation locks.
            .select_related("owner", "operation")
            .filter(id=advertisement_id, owner=owner)
            .first()
        )
        if not advertisement:
            raise AdvertisingServiceError("Advertisement not found.", status_code=404)
        if not advertisement.owner.is_active:
            raise AdvertisingServiceError(
                "This account is not eligible to publish advertisements.",
                status_code=403,
            )
        expected_operation_id = f"{advertisement.operation.operation_id}-payment"
        if operation_id != expected_operation_id:
            raise AdvertisingServiceError(
                "The payment operation ID does not match this advertisement.",
                errors={"operation_id": ["invalid_payment_operation"]},
            )
        if payment_mode != MockAdvertisementPayment.MODE_MOCK:
            raise AdvertisingServiceError(
                "Only simulated payment is available.",
                errors={"payment_mode": ["unsupported"]},
            )
        existing = MockAdvertisementPayment.objects.filter(
            advertisement=advertisement
        ).first()
        if existing:
            if (
                existing.operation_id != operation_id
                or existing.payment_mode != payment_mode
                or existing.status != MockAdvertisementPayment.STATUS_SUCCEEDED
            ):
                raise AdvertisingServiceError(
                    "This advertisement cannot be activated from its current state.",
                    status_code=409,
                    errors={"status": ["invalid_transition"]},
                )
            return advertisement, existing, False
        # New collections must originate from a reviewed, shared invoice.
        # The old endpoint remains useful for replaying historical ad receipts.
        from core_apps.features.providers import checkout_available

        if not checkout_available():
            raise AdvertisingServiceError(
                "Simulated payment is unavailable.", status_code=403
            )
        if (
            invoice is None
            or attempt is None
            or invoice.purpose != "advertising"
            or invoice.purchase_snapshot.get("subject_id") != str(advertisement.id)
            or invoice.payer_id != owner.pk
            or attempt.invoice_id != invoice.pk
        ):
            raise AdvertisingServiceError(
                "Review the advertisement invoice before paying.",
                status_code=409,
                errors={"invoice": ["invoice_required"]},
            )
        if advertisement.status != Advertisement.Status.PENDING_PAYMENT:
            raise AdvertisingServiceError(
                "This advertisement cannot be activated from its current state.",
                status_code=409,
                errors={"status": ["invalid_transition"]},
            )
        if not destination_is_eligible(advertisement):
            raise AdvertisingServiceError(
                "The advertisement destination is no longer eligible.",
                errors={"property_id": ["not_eligible"]},
            )
        if not media_is_available(advertisement):
            raise AdvertisingServiceError(
                "The advertisement media is unavailable.",
                errors={"banner": ["unavailable"]},
            )
        now = timezone.now()
        snapshot = advertisement.plan_snapshot
        advertisement.starts_at = now
        advertisement.ends_at = calendar_expiry(
            now, snapshot["duration_unit"], int(snapshot["duration_count"])
        )
        advertisement.activated_at = now
        advertisement.expiration_processed_at = None
        advertisement.status = Advertisement.Status.ACTIVE
        advertisement.save(
            update_fields=[
                "starts_at",
                "ends_at",
                "activated_at",
                "expiration_processed_at",
                "status",
                "updated_at",
            ]
        )
        payment = MockAdvertisementPayment.objects.create(
            advertisement=advertisement,
            operation_id=operation_id,
            payment_mode=payment_mode,
        )
        return advertisement, payment, True


def is_publicly_eligible(advertisement, now=None):
    now = now or timezone.now()
    payment = getattr(advertisement, "payment", None)
    from core_apps.features.models import PaymentFulfillment

    confirmed = bool(
        payment
        and payment.status == MockAdvertisementPayment.STATUS_SUCCEEDED
        and payment.payment_mode == MockAdvertisementPayment.MODE_MOCK
    )
    confirmed = (
        confirmed
        or PaymentFulfillment.objects.filter(
            invoice__purpose="advertising",
            invoice__purchase_snapshot__subject_id=str(advertisement.id),
            invoice__payer=advertisement.owner,
            invoice__status="paid",
            status="fulfilled",
            attempt__payment_status="captured",
        ).exists()
    )
    return bool(
        advertisement.status == Advertisement.Status.ACTIVE
        and advertisement.placement == Advertisement.PLACEMENT_TENANT_HOME
        and advertisement.starts_at
        and advertisement.ends_at
        and advertisement.starts_at <= now < advertisement.ends_at
        and advertisement.owner.is_active
        and confirmed
        and destination_is_eligible(advertisement)
        and media_is_available(advertisement)
    )
