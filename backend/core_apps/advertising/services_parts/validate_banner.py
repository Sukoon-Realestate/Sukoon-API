"""Services: validate banner."""

import hashlib
import json
import warnings
from io import BytesIO
from zoneinfo import ZoneInfo
from PIL import Image, UnidentifiedImageError
from core_apps.properties.models import Property


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
