"""Durable upload intents, authenticated bytes and independent asset-media review."""

import hashlib
import io
from PIL import Image, UnidentifiedImageError
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, PermissionDenied
from core_apps.properties.models import ResidentialMedia
from core_apps.virtual_tours import storage
from ..rental_lifecycle.common import audit, require_revision, require_staff
from ..rental_phase2 import RentalConflict
from .portfolio import parent_for

MAX_BYTES = 5 * 1024 * 1024


def media_for(user, identity, lock=False):
    qs = (
        ResidentialMedia.objects.select_for_update()
        if lock
        else ResidentialMedia.objects
    )
    return get_object_or_404(qs, id=identity, owner=user)


def payload(item):
    return {
        "id": str(item.id),
        "revision": item.revision,
        "request_key": str(item.request_key),
        "purpose": item.purpose,
        "caption": item.caption,
        "representative": item.representative,
        "sha256": item.sha256,
        "byte_size": item.byte_size,
        "content_type": item.content_type,
        "state": item.state,
        "review_status": item.review_status,
        "review_reason": item.review_reason,
        "asset_id": str(item.building.id if item.building_id else item.complex.id),
        "asset_kind": "building" if item.building_id else "complex",
    }


@transaction.atomic
def create_intent(user, kind, identity, data):
    parent = parent_for(user, kind, identity, lock=True)
    require_revision(parent, data["expected_revision"])
    if parent.media.exclude(state="removed").count() >= 60:
        raise ValidationError("Remove unused media before adding more files.")
    item = ResidentialMedia.objects.create(
        owner=user,
        **{kind: parent},
        **{
            k: data[k]
            for k in (
                "request_key",
                "purpose",
                "caption",
                "representative",
                "sha256",
                "byte_size",
                "content_type",
            )
        }
    )
    audit(item, user, "portfolio_media_intent_created")
    return item


def upload(user, identity, uploaded):
    item = media_for(user, identity)
    if item.state == "ready":
        return item
    if item.state != "pending" or not uploaded or uploaded.size != item.byte_size:
        raise ValidationError("Select the original file for this upload intent.")
    raw = uploaded.read(MAX_BYTES + 1)
    if len(raw) != item.byte_size or hashlib.sha256(raw).hexdigest() != item.sha256:
        raise ValidationError("The file does not match the saved upload identity.")
    try:
        with Image.open(io.BytesIO(raw)) as image:
            if (
                image.format not in {"JPEG", "PNG"}
                or image.width * image.height > 24000000
                or image.format
                != ("PNG" if item.content_type == "image/png" else "JPEG")
            ):
                raise ValueError("invalid image")
            image.load()
            # Re-encode to strip EXIF/GPS and embedded metadata before any serving.
            cleaned = io.BytesIO()
            image.convert("RGB").save(cleaned, format="PNG")
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ValidationError(
            "Choose a valid PNG or JPEG image within the pixel limit."
        )
    # Provider I/O is outside database locks. The durable pending row is the retry
    # identity; a lost response is resolved by GET before another transmission.
    key, _, _ = storage.write_blob([cleaned.getvalue()], 32 * 1024 * 1024)
    with transaction.atomic():
        item = media_for(user, identity, lock=True)
        if item.state == "pending":
            item.blob, item.state = key, "ready"
            item.revision += 1
            item.save()
            audit(item, user, "portfolio_media_uploaded")
        elif item.state != "ready":
            raise RentalConflict("This upload was removed.", code="media_removed")
    return item


@transaction.atomic
def remove(user, identity, data):
    item = media_for(user, identity, lock=True)
    require_revision(item, data["expected_revision"])
    item.state = "removed"
    item.revision += 1
    item.save()
    # Keep private evidence and historical review references; revoke byte access.
    audit(item, user, "portfolio_media_removed")
    return item


@transaction.atomic
def review(user, identity, data):
    require_staff(user, {"property_reviewer"})
    item = get_object_or_404(ResidentialMedia.objects.select_for_update(), id=identity)
    if item.owner_id == user.pk:
        raise PermissionDenied("An independent reviewer must review this media.")
    require_revision(item, data["expected_revision"])
    if item.state != "ready":
        raise RentalConflict(
            "Only completed uploads can be reviewed.", code="media_incomplete"
        )
    item.review_status, item.review_reason, item.reviewed_by = (
        data["status"],
        data["reason"],
        user,
    )
    item.revision += 1
    item.save()
    audit(
        item,
        user,
        "portfolio_media_reviewed",
        data["reason"],
        {"status": data["status"], "purpose": item.purpose},
    )
    return item
