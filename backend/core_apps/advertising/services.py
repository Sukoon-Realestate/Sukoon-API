import calendar
import hashlib
import json
import warnings
from datetime import datetime, timedelta, timezone as datetime_timezone
from io import BytesIO
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.utils import timezone
from PIL import Image, UnidentifiedImageError

from core_apps.properties.models import Property

from .models import (
    Advertisement,
    AdvertisementMedia,
    AdvertisementOperation,
    AdvertisingPlan,
    MockAdvertisementPayment,
)


CAIRO = ZoneInfo("Africa/Cairo")
MAX_BANNER_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


class AdvertisingServiceError(Exception):
    def __init__(self, message, *, status_code=400, errors=None):
        self.message = message
        self.status_code = status_code
        self.errors = errors
        super().__init__(message)


def translated_plan_title(plan, language):
    return plan.title_ar if str(language).startswith("ar") else plan.title_en


def plan_payload(plan, language):
    return {
        "id": plan.id,
        "title": translated_plan_title(plan, language),
        "duration_unit": plan.duration_unit,
        "duration_count": plan.duration_count,
        "revision": plan.revision,
        "active": plan.active,
        "price": {
            "amount_minor": plan.amount_minor,
            "currency": plan.currency,
            "exponent": plan.exponent,
        },
    }


def validate_banner(upload):
    if upload.size > MAX_BANNER_BYTES:
        raise AdvertisingServiceError(
            "The banner must not exceed 10 MiB.",
            status_code=413,
            errors={"banner": ["too_large"]},
        )
    raw = upload.read()
    upload.seek(0)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                image.verify()
                image_format = image.format
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise AdvertisingServiceError(
            "The banner is not a valid supported image.",
            status_code=415,
            errors={"banner": ["invalid_image"]},
        )
    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise AdvertisingServiceError(
            "Only JPEG, PNG, and WebP banners are supported.",
            status_code=415,
            errors={"banner": ["unsupported_type"]},
        )
    return raw, hashlib.sha256(raw).hexdigest(), ALLOWED_IMAGE_FORMATS[image_format]


def property_is_publishable(property_obj):
    return bool(
        property_obj
        and property_obj.owner.is_active
        and property_obj.status == Property.Status.VERIFIED
    )


def eligible_offer(property_obj, offer_id):
    if not offer_id:
        return True
    for offer in (property_obj.rental_inventory or {}).get("offers", []):
        if str(offer.get("id")) == str(offer_id):
            return (
                not offer.get("archived", False)
                and offer.get("availability", "available") == "available"
            )
    return False


def validate_destination(owner, property_id, offer_id):
    if not property_id:
        return None
    property_obj = (
        Property.objects.select_related("owner")
        .filter(id=property_id, owner=owner)
        .first()
    )
    if not property_is_publishable(property_obj):
        raise AdvertisingServiceError(
            "The selected property is not eligible for publication.",
            errors={"property_id": ["not_eligible"]},
        )
    if not eligible_offer(property_obj, offer_id):
        raise AdvertisingServiceError(
            "The selected offer is not eligible for publication.",
            errors={"offer_id": ["not_eligible"]},
        )
    return property_obj


def payload_fingerprint(attrs, banner_sha256):
    canonical = {
        "plan_id": attrs["plan_id"],
        "plan_revision": attrs["plan_revision"],
        "title": attrs["title"],
        "description": attrs.get("description", ""),
        "property_id": str(attrs.get("property_id") or ""),
        "offer_id": attrs.get("offer_id", ""),
        "banner_sha256": banner_sha256,
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def create_advertisement(owner, attrs, language):
    raw, banner_sha256, content_type = validate_banner(attrs["banner"])
    fingerprint = payload_fingerprint(attrs, banner_sha256)
    operation_id = attrs["operation_id"]

    saved_media = None
    try:
        with transaction.atomic():
            operation = (
                AdvertisementOperation.objects.select_for_update()
                .filter(owner=owner, operation_id=operation_id)
                .first()
            )
            if operation:
                if operation.state == AdvertisementOperation.State.FOUND:
                    if operation.payload_fingerprint != fingerprint:
                        raise AdvertisingServiceError(
                            "This operation ID was already used with different data.",
                            status_code=409,
                            errors={"operation_id": ["idempotency_conflict"]},
                        )
                    return operation.advertisement, False
                if operation.state == AdvertisementOperation.State.PROCESSING:
                    raise AdvertisingServiceError(
                        "This operation is still processing.",
                        status_code=409,
                        errors={"operation_id": ["operation_processing"]},
                    )
                operation.payload_fingerprint = fingerprint
                operation.state = AdvertisementOperation.State.PROCESSING
                operation.retry_allowed = False
                operation.rejection_errors = None
                operation.save()
            else:
                try:
                    operation = AdvertisementOperation.objects.create(
                        owner=owner,
                        operation_id=operation_id,
                        state=AdvertisementOperation.State.PROCESSING,
                        payload_fingerprint=fingerprint,
                    )
                except IntegrityError:
                    raise AdvertisingServiceError(
                        "This operation is already being processed.",
                        status_code=409,
                        errors={"operation_id": ["operation_processing"]},
                    )

            plan = (
                AdvertisingPlan.objects.select_for_update()
                .filter(id=attrs["plan_id"], active=True)
                .first()
            )
            if not plan:
                raise AdvertisingServiceError(
                    "The selected plan is unavailable.",
                    errors={"plan_id": ["not_available"]},
                )
            if plan.revision != attrs["plan_revision"]:
                raise AdvertisingServiceError(
                    "The selected plan changed. Review the current plan before continuing.",
                    status_code=409,
                    errors={"plan_revision": ["plan_changed"]},
                )
            property_obj = validate_destination(
                owner, attrs.get("property_id"), attrs.get("offer_id", "")
            )
            snapshot = plan_payload(plan, language)
            advertisement = Advertisement.objects.create(
                owner=owner,
                operation=operation,
                title=attrs["title"],
                description=attrs.get("description", ""),
                property=property_obj,
                offer_id=attrs.get("offer_id", ""),
                plan_snapshot=snapshot,
            )
            upload = attrs["banner"]
            upload.seek(0)
            saved_media = AdvertisementMedia.objects.create(
                advertisement=advertisement,
                banner=upload,
                sha256=banner_sha256,
                content_type=content_type,
                size_bytes=len(raw),
            )
            operation.state = AdvertisementOperation.State.FOUND
            operation.save(update_fields=["state", "updated_at"])
            return advertisement, True
    except Exception:
        if saved_media and saved_media.banner.name:
            try:
                saved_media.banner.storage.delete(saved_media.banner.name)
            except Exception:
                pass
        raise


def record_rejected_operation(owner, operation_id, errors):
    if not operation_id or len(str(operation_id)) > 128:
        return
    serializable_errors = (
        json.loads(json.dumps(errors, default=str)) if errors else None
    )
    with transaction.atomic():
        operation = (
            AdvertisementOperation.objects.select_for_update()
            .filter(owner=owner, operation_id=operation_id)
            .first()
        )
        if operation and operation.state in {
            AdvertisementOperation.State.FOUND,
            AdvertisementOperation.State.PROCESSING,
        }:
            return
        if operation:
            operation.retry_allowed = True
            operation.rejection_errors = serializable_errors
            operation.save(
                update_fields=["retry_allowed", "rejection_errors", "updated_at"]
            )
        else:
            try:
                with transaction.atomic():
                    AdvertisementOperation.objects.create(
                        owner=owner,
                        operation_id=operation_id,
                        state=AdvertisementOperation.State.REJECTED,
                        retry_allowed=True,
                        rejection_errors=serializable_errors,
                    )
            except IntegrityError:
                return


def _valid_local_datetime(naive, fold):
    aware = naive.replace(tzinfo=CAIRO, fold=fold)
    round_trip = aware.astimezone(datetime_timezone.utc).astimezone(CAIRO)
    return aware if round_trip.replace(tzinfo=None) == naive else None


def resolve_cairo_local(naive):
    valid = [
        value
        for value in (_valid_local_datetime(naive, 0), _valid_local_datetime(naive, 1))
        if value
    ]
    if valid:
        return max(valid, key=lambda value: value.astimezone(datetime_timezone.utc))
    before = naive.replace(tzinfo=CAIRO, fold=0).utcoffset()
    after = naive.replace(tzinfo=CAIRO, fold=1).utcoffset()
    if before is not None and after is not None and after > before:
        shifted = naive + (after - before)
        valid = [
            value
            for value in (
                _valid_local_datetime(shifted, 0),
                _valid_local_datetime(shifted, 1),
            )
            if value
        ]
        if valid:
            return max(valid, key=lambda value: value.astimezone(datetime_timezone.utc))
    probe = naive
    for _ in range(180):
        probe += timedelta(minutes=1)
        valid = [
            value
            for value in (
                _valid_local_datetime(probe, 0),
                _valid_local_datetime(probe, 1),
            )
            if value
        ]
        if valid:
            return max(valid, key=lambda value: value.astimezone(datetime_timezone.utc))
    raise ValueError("Unable to resolve Cairo local datetime")


def calendar_expiry(starts_at, duration_unit, duration_count):
    if duration_unit == AdvertisingPlan.DurationUnit.WEEK:
        return starts_at + timedelta(days=7 * duration_count)
    local = starts_at.astimezone(CAIRO)
    year, month = local.year, local.month
    if duration_unit == AdvertisingPlan.DurationUnit.CALENDAR_MONTH:
        month_index = month - 1 + duration_count
        target_year = year + month_index // 12
        target_month = month_index % 12 + 1
    elif duration_unit == AdvertisingPlan.DurationUnit.CALENDAR_YEAR:
        target_year = year + duration_count
        target_month = month
    else:
        raise ValueError("Unsupported duration unit")
    target_day = min(local.day, calendar.monthrange(target_year, target_month)[1])
    naive = datetime(
        target_year,
        target_month,
        target_day,
        local.hour,
        local.minute,
        local.second,
        local.microsecond,
    )
    return resolve_cairo_local(naive).astimezone(datetime_timezone.utc)


def activate_with_mock_payment(owner, advertisement_id, operation_id, payment_mode):
    with transaction.atomic():
        advertisement = (
            Advertisement.objects.select_for_update()
            .select_related("owner", "property__owner", "operation")
            .filter(id=advertisement_id, owner=owner)
            .first()
        )
        if not advertisement:
            raise AdvertisingServiceError("Advertisement not found.", status_code=404)
        existing = MockAdvertisementPayment.objects.filter(
            advertisement=advertisement
        ).first()
        if existing:
            return advertisement, existing, False
        if not owner.is_active:
            raise AdvertisingServiceError(
                "This account is not eligible to publish advertisements.",
                status_code=403,
            )
        if advertisement.status != Advertisement.Status.PENDING_PAYMENT:
            raise AdvertisingServiceError(
                "This advertisement cannot be activated from its current state.",
                status_code=409,
                errors={"status": ["invalid_transition"]},
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
        if advertisement.property and (
            not property_is_publishable(advertisement.property)
            or not eligible_offer(advertisement.property, advertisement.offer_id)
        ):
            raise AdvertisingServiceError(
                "The advertisement destination is no longer eligible.",
                errors={"property_id": ["not_eligible"]},
            )
        if not hasattr(advertisement, "media") or not advertisement.media.banner:
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
        advertisement.status = Advertisement.Status.ACTIVE
        advertisement.save(
            update_fields=[
                "starts_at",
                "ends_at",
                "activated_at",
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


def effective_status(advertisement, now=None):
    now = now or timezone.now()
    if (
        advertisement.status
        in {Advertisement.Status.ACTIVE, Advertisement.Status.EXPIRED}
        and advertisement.ends_at
        and now >= advertisement.ends_at
    ):
        return Advertisement.Status.EXPIRED
    return advertisement.status


def destination_is_eligible(advertisement):
    if not advertisement.property_id:
        return True
    return property_is_publishable(advertisement.property) and eligible_offer(
        advertisement.property, advertisement.offer_id
    )
