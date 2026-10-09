import calendar
import hashlib
import json
from datetime import date, timedelta

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from ..models import (
    IdempotencyRecord,
    OwnerPaymentProfile,
    RentalCommercialPolicy,
    RentalInventoryDayLock,
)


class RentalConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "rental_conflict"
    default_detail = "The rental operation conflicts with current server state."


def fingerprint(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()


def replay_operation(user, operation, request_key, payload):
    record = IdempotencyRecord.objects.filter(
        user=user, operation=operation, request_key=str(request_key)
    ).first()
    if not record:
        return None
    if record.fingerprint != fingerprint(payload):
        raise RentalConflict(
            "This request_key was already used for a different intention.",
            code="idempotency_conflict",
        )
    return record.response_data, record.response_status


def remember_mutation(
    *,
    user,
    operation,
    request_key,
    payload,
    request_subject_id,
    result_subject_id,
    result_revision,
    resource,
    response_status=200,
):
    record = IdempotencyRecord.objects.create(
        user=user,
        operation=operation,
        request_key=str(request_key),
        fingerprint=fingerprint(payload),
        response_data={},
        response_status=response_status,
        is_rental_operation=True,
        request_subject_id=request_subject_id,
        result_subject_id=result_subject_id,
        result_revision=result_revision,
    )
    response_data = {
        "resource": resource,
        "operation_receipt": {
            "id": str(record.id),
            "subject_id": str(result_subject_id),
            "request_key": str(request_key),
            "revision": result_revision,
            "status": "confirmed",
        },
    }
    record.response_data = response_data
    record.save(update_fields=["response_data", "updated_at"])
    return response_data


def ensure_policy():
    policy, _ = RentalCommercialPolicy.objects.get_or_create(
        version="rental-policy-v1",
        defaults={
            "summary": {
                "commission": "10% of first-period base rent, paid by owner",
                "tenant_service_fee": "0 EGP",
                "processing_fee_payer": "platform",
                "renewal_commission": "0%",
            }
        },
    )
    return policy


def get_or_create_owner_profile(owner):
    ensure_policy()
    profile, _ = OwnerPaymentProfile.objects.get_or_create(
        owner=owner,
        defaults={
            "provider": getattr(settings, "RENTAL_PROVIDER_BACKEND", "disabled")
            if getattr(settings, "RENTAL_PROVIDER_BACKEND", "disabled") != "disabled"
            else "",
            "requirements": ["beneficiary", "identity_verification"],
        },
    )
    return profile


def assert_owner_ready(owner, property_obj=None):
    if not owner.is_active or not owner.is_verified:
        raise PermissionDenied(
            {"message": "A verified active owner is required.", "code": "account_verification_required"}
        )
    if property_obj and (
        property_obj.owner_id != owner.pk
        or not property_obj.is_verified
        or not property_obj.is_ownership_verified
    ):
        raise PermissionDenied(
            {"message": "Verified listing ownership is required.", "code": "capability_unavailable"}
        )
    profile = get_or_create_owner_profile(owner)
    if (
        profile.status != OwnerPaymentProfile.Status.READY
        or not profile.payout_ready
        or "rental-policy-v1" not in profile.accepted_policy_versions
    ):
        raise PermissionDenied(
            {"message": "Owner beneficiary onboarding is incomplete.", "code": "account_verification_required"}
        )
    return profile


def add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def validate_interest_capacity(snapshot, occupants):
    capacity = snapshot.get("capacity")
    if capacity is not None and occupants > capacity:
        raise ValidationError({"occupants": "The selected offer cannot hold this party."})


def reserve_inventory_days(lease, starts_on, ends_on_exclusive, expires_at):
    if ends_on_exclusive <= starts_on:
        raise ValidationError({"ends_on_exclusive": "Must be after starts_on."})
    now = timezone.now()
    RentalInventoryDayLock.objects.filter(
        kind=RentalInventoryDayLock.Kind.HOLD,
        expires_at__lte=now,
    ).delete()
    days = []
    current = starts_on
    while current < ends_on_exclusive:
        days.append(
            RentalInventoryDayLock(
                property=lease.property,
                offer_id=lease.offer_id,
                stay_on=current,
                kind=RentalInventoryDayLock.Kind.HOLD,
                lease=lease,
                expires_at=expires_at,
            )
        )
        current += timedelta(days=1)
    try:
        RentalInventoryDayLock.objects.bulk_create(days)
    except IntegrityError:
        raise RentalConflict(
            "The accommodation is no longer available for those dates.",
            code="offer_unavailable",
        )


def activate_inventory(lease):
    updated = RentalInventoryDayLock.objects.filter(
        lease=lease,
        kind=RentalInventoryDayLock.Kind.HOLD,
        expires_at__gt=timezone.now(),
    ).update(kind=RentalInventoryDayLock.Kind.OCCUPIED, expires_at=None)
    if not updated:
        raise RentalConflict("The inventory hold has expired.", code="hold_expired")
