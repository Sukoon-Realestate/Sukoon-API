"""Reserve and finalize briefly; never hold account/property locks over Cloudinary."""

import hashlib
from datetime import timedelta

import cloudinary
import cloudinary.api
import cloudinary.uploader
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from core_apps.common.idempotency import fingerprint, IdempotencyConflict
from core_apps.features.models import IdempotencyRecord
from core_apps.users.models import User
from core_apps.users.services.sessions import validate_session
from ..models import Property, PropertyImage


class UploadPending(APIException):
    status_code = 503
    default_code = "upload_unconfirmed"
    default_detail = (
        "Upload confirmation is pending. Check the original upload before retrying."
    )


def _serialize(image):
    from ..serializers import PropertyImageSerializer

    return {
        "message": "Image uploaded successfully.",
        **PropertyImageSerializer(image).data,
    }


def _authority(current, prop, claims, reservation=None):
    if claims:
        validate_session(current, claims)
    if (
        not current.is_active
        or prop.retired_at
        or (prop.owner_id != current.pk and not current.is_staff)
    ):
        raise PermissionDenied("Only the current owner can upload listing media.")
    if reservation and (
        current.security_epoch != reservation["security_epoch"]
        or reservation.get("requires_verified", True)
        and not current.is_verified
    ):
        raise PermissionDenied("Upload authority changed. Review the property.")


def _finalize(record_id, resource, user, claims, *, recovery=False):
    with transaction.atomic():
        current = User.objects.select_for_update().get(pk=user.pk)
        record = IdempotencyRecord.objects.get(pk=record_id)
        prop = Property.objects.select_for_update().get(id=record.request_subject_id)
        record = IdempotencyRecord.objects.select_for_update().get(pk=record_id)
        _authority(current, prop, claims)
        if record.recovery_status == "confirmed":
            return record.response_data, record.response_status, True
        if record.recovery_status == "absent_final":
            raise IdempotencyConflict()
        data = record.response_data
        _authority(current, prop, claims, data)
        if not recovery and record.created_at < timezone.now() - timedelta(minutes=15):
            raise UploadPending()
        if (
            resource.get("public_id") != data["public_id"]
            or resource.get("resource_type", "image") != "image"
        ):
            raise UploadPending()
        last = prop.images.aggregate(last=Max("position"))["last"]
        image = PropertyImage.objects.create(
            property=prop,
            image=cloudinary.CloudinaryImage(
                public_id=resource["public_id"],
                version=resource.get("version"),
                format=resource.get("format"),
                type="upload",
            ),
            name=data["name"],
            description=data["description"],
            position=0 if last is None else last + 1,
        )
        record.response_data, record.response_status = _serialize(image), 201
        record.result_subject_id, record.recovery_status = image.id, "confirmed"
        record.save()
        return record.response_data, 201, False


def upload(*, user, claims, property_obj, key, data, require_verified=True):
    operation = f"property.image.upload:{property_obj.id}"
    digest = fingerprint(data)
    with transaction.atomic():
        current = User.objects.select_for_update().get(pk=user.pk)
        prop = Property.objects.select_for_update().get(pk=property_obj.pk)
        _authority(current, prop, claims)
        if require_verified and not current.is_verified:
            raise PermissionDenied(
                "Identity verification is required for recoverable image uploads."
            )
        record = IdempotencyRecord.objects.filter(
            user=current, operation=operation, request_key=key
        ).first()
        if record:
            if record.fingerprint != digest or record.recovery_status == "absent_final":
                raise IdempotencyConflict()
            if record.recovery_status == "confirmed":
                return record.response_data, record.response_status, True
            raise UploadPending()
        pending = IdempotencyRecord.objects.filter(
            operation=operation, recovery_status__in=["pending", "unknown"]
        ).count()
        if prop.images.count() + pending >= 25:
            raise ValidationError("A property cannot have more than 25 images.")
        public_id = (
            "properties/images/"
            + hashlib.sha256(f"{current.pk}:{operation}:{key}".encode()).hexdigest()
        )
        record = IdempotencyRecord.objects.create(
            user=current,
            operation=operation,
            request_key=key,
            fingerprint=digest,
            request_subject_id=prop.id,
            recovery_status="pending",
            response_status=503,
            response_data={
                "public_id": public_id,
                "name": data.get("name", "").strip(),
                "description": data.get("description", "").strip(),
                "security_epoch": current.security_epoch,
                "requires_verified": require_verified,
            },
        )
    try:
        data["image"].seek(0)
        resource = cloudinary.uploader.upload(
            data["image"],
            public_id=public_id,
            resource_type="image",
            overwrite=False,
            unique_filename=False,
            timeout=120,
        )
        return _finalize(record.pk, resource, user, claims)
    except Exception:
        IdempotencyRecord.objects.filter(
            pk=record.pk, recovery_status="pending"
        ).update(recovery_status="unknown")
        raise UploadPending()


def reconcile(*, user, claims, property_id, key):
    """Discover lost provider acknowledgment without repeating the upload."""
    record = IdempotencyRecord.objects.filter(
        user=user,
        operation=f"property.image.upload:{property_id}",
        request_key=key,
        recovery_status__in=["pending", "unknown"],
    ).first()
    if not record:
        return
    current = User.objects.get(pk=user.pk)
    prop = Property.objects.get(id=property_id)
    _authority(current, prop, claims, record.response_data)
    try:
        resource = cloudinary.api.resource(
            record.response_data["public_id"], resource_type="image", timeout=10
        )
    except cloudinary.exceptions.NotFound:
        if record.created_at < timezone.now() - timedelta(minutes=15):
            with transaction.atomic():
                current = User.objects.select_for_update().get(pk=user.pk)
                prop = Property.objects.select_for_update().get(id=property_id)
                stored = IdempotencyRecord.objects.select_for_update().get(pk=record.pk)
                if stored.recovery_status in ["pending", "unknown"]:
                    _authority(current, prop, claims, stored.response_data)
                    stored.recovery_status = "absent_final"
                    stored.save(update_fields=["recovery_status"])
        return
    except Exception:
        return
    # Recheck authority under locks after the slow provider read.
    _finalize(record.pk, resource, user, claims, recovery=True)
