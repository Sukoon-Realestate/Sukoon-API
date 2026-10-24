from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

import cloudinary.exceptions
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, connections
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.common.idempotency import IdempotencyConflict
from core_apps.features.models import IdempotencyRecord
from core_apps.users.models import User
from core_apps.properties.models import PropertyImage
from core_apps.properties.services.image_uploads import (
    upload,
    reconcile,
    UploadPending,
    _finalize,
)
from .test_discovery_fixes import listing

pytestmark = pytest.mark.django_db(transaction=True)


def image():
    return {
        "image": SimpleUploadedFile(
            "room.jpg", b"synthetic-provider-input", content_type="image/jpeg"
        )
    }


def resource(public_id):
    return {
        "public_id": public_id,
        "resource_type": "image",
        "format": "jpg",
        "version": 1,
    }


@pytest.fixture
def owner(user):
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    return user


def test_replay_and_changed_bytes_do_not_upload_twice(owner, listing):
    with patch(
        "cloudinary.uploader.upload",
        side_effect=lambda *args, **kwargs: resource(kwargs["public_id"]),
    ) as remote:
        first = upload(
            user=owner, claims=None, property_obj=listing, key="same", data=image()
        )
        second = upload(
            user=owner, claims=None, property_obj=listing, key="same", data=image()
        )
        assert first[0]["id"] == second[0]["id"] and second[2]
        with pytest.raises(IdempotencyConflict):
            upload(
                user=owner,
                claims=None,
                property_obj=listing,
                key="same",
                data={"image": SimpleUploadedFile("room.jpg", b"different")},
            )
    assert remote.call_count == 1 and listing.images.count() == 1


def test_lost_response_reconciles_original_resource(owner, listing):
    with patch("cloudinary.uploader.upload", side_effect=TimeoutError):
        with pytest.raises(UploadPending):
            upload(
                user=owner, claims=None, property_obj=listing, key="lost", data=image()
            )
    record = IdempotencyRecord.objects.get(request_key="lost")
    assert record.recovery_status == "unknown" and not listing.images.exists()
    with patch(
        "cloudinary.api.resource",
        return_value=resource(record.response_data["public_id"]),
    ):
        reconcile(user=owner, claims=None, property_id=listing.id, key="lost")
        reconcile(user=owner, claims=None, property_id=listing.id, key="lost")
    assert listing.images.count() == 1


def test_recovery_rechecks_authority_after_provider_read(owner, listing):
    with patch("cloudinary.uploader.upload", side_effect=TimeoutError):
        with pytest.raises(UploadPending):
            upload(
                user=owner,
                claims=None,
                property_obj=listing,
                key="revoke",
                data=image(),
            )
    record = IdempotencyRecord.objects.get(request_key="revoke")

    def revoked(*args, **kwargs):
        User.objects.filter(pk=owner.pk).update(security_epoch=1)
        return resource(record.response_data["public_id"])

    with patch("cloudinary.api.resource", side_effect=revoked), pytest.raises(
        PermissionDenied
    ):
        reconcile(user=owner, claims=None, property_id=listing.id, key="revoke")
    assert not listing.images.exists()


def test_absent_final_fences_late_worker(owner, listing):
    with patch("cloudinary.uploader.upload", side_effect=TimeoutError), pytest.raises(
        UploadPending
    ):
        upload(user=owner, claims=None, property_obj=listing, key="late", data=image())
    record = IdempotencyRecord.objects.get(request_key="late")
    IdempotencyRecord.objects.filter(pk=record.pk).update(
        created_at=timezone.now() - timedelta(minutes=16)
    )
    with patch(
        "cloudinary.api.resource", side_effect=cloudinary.exceptions.NotFound("absent")
    ):
        reconcile(user=owner, claims=None, property_id=listing.id, key="late")
    with pytest.raises(IdempotencyConflict):
        _finalize(record.pk, resource(record.response_data["public_id"]), owner, None)
    assert not listing.images.exists()


def test_pending_reservations_count_towards_image_limit(owner, listing):
    PropertyImage.objects.bulk_create(
        [PropertyImage(property=listing, image=f"existing-{i}") for i in range(24)]
    )
    with patch("cloudinary.uploader.upload", side_effect=TimeoutError), pytest.raises(
        UploadPending
    ):
        upload(
            user=owner, claims=None, property_obj=listing, key="slot25", data=image()
        )
    with patch("cloudinary.uploader.upload") as remote, pytest.raises(ValidationError):
        upload(
            user=owner, claims=None, property_obj=listing, key="slot26", data=image()
        )
    remote.assert_not_called()


def test_remote_uploads_overlap_without_holding_account_lock(owner, listing):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks")
    barrier = Barrier(2)

    def provider(*args, **kwargs):
        barrier.wait(timeout=10)
        return resource(kwargs["public_id"])

    def work(key):
        try:
            return upload(
                user=owner, claims=None, property_obj=listing, key=key, data=image()
            )
        finally:
            connections.close_all()

    with patch("cloudinary.uploader.upload", side_effect=provider):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(work, ["parallel1", "parallel2"]))
    assert all(item[1] == 201 for item in results)
    assert listing.images.count() == 2
    assert list(
        listing.images.order_by("position").values_list("position", flat=True)
    ) == [0, 1]
