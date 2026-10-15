import io
from datetime import timedelta
from unittest.mock import patch
import pytest
from django.utils import timezone
from botocore.response import StreamingBody
from core_apps.virtual_tours import remote_storage, storage, uploads
from core_apps.virtual_tours.errors import TourError
from core_apps.virtual_tours.models import TourUploadSession
from .test_tours import synthetic_draft


class FakePrivateBucket:
    """Protocol fake: never contacts AWS or a real Space."""

    def __init__(self):
        self.objects = {}
        self.deleted = []
        self.modified = timezone.now() - timedelta(days=8)

    def put_object(self, **params):
        assert params["CacheControl"] == "private, no-store"
        assert "ACL" not in params
        assert params["Bucket"] == "synthetic-private-tour-bucket"
        content = params["Body"].read()
        assert len(content) == params["ContentLength"]
        self.objects[params["Key"]] = content

    def get_object(self, **params):
        content = self.objects[params["Key"]]
        return {
            "Body": StreamingBody(io.BytesIO(content), len(content)),
            "ContentLength": len(content),
        }

    def get_paginator(self, name):
        assert name == "list_objects_v2"
        return self

    def paginate(self, **params):
        yield {
            "Contents": [
                {"Key": key, "LastModified": self.modified}
                for key in self.objects
                if key.startswith(params["Prefix"])
            ]
        }

    def delete_object(self, **params):
        self.deleted.append(params["Key"])


@pytest.fixture
def bucket(settings):
    settings.VIRTUAL_TOUR_S3_BUCKET = "synthetic-private-tour-bucket"
    settings.VIRTUAL_TOUR_S3_PREFIX = "test-tour-prefix"
    value = FakePrivateBucket()
    with patch.object(remote_storage, "client", return_value=value):
        yield value


@pytest.mark.django_db
def test_remote_upload_completion_survives_loss_of_api_local_files(
    property_obj, settings, tmp_path, bucket
):
    _, revision, _ = synthetic_draft(property_obj)
    import hashlib

    content = b"synthetic part bytes"
    result, _ = uploads.create_upload(
        revision,
        {
            "role": "panorama",
            "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "media_type": "image/jpeg",
        },
        '"draft-2"',
    )
    upload = TourUploadSession.objects.get(id=result["id"])
    uploads.receive_part(upload, 1, [content])
    staging_key = upload.parts["1"]["blob"]
    settings.VIRTUAL_TOUR_PRIVATE_ROOT = str(tmp_path / "different-api-instance")
    result, _ = uploads.complete(upload)
    upload.refresh_from_db()
    assert result["asset_id"] == str(upload.asset.id)
    assert staging_key != upload.asset.blob
    assert storage.read_path(upload.asset.blob).read_bytes() == content
    assert bucket.objects[remote_storage.object_key(staging_key)] == content
    assert bucket.objects[remote_storage.object_key(upload.asset.blob)] == content


def test_remote_tiles_survive_loss_of_worker_local_files(settings, tmp_path, bucket):
    key = "a" * 32
    storage.path(key).mkdir()
    (storage.path(key) / "f_0_0_0.jpg").write_bytes(b"synthetic tile")
    storage.persist_tiles(key)
    settings.VIRTUAL_TOUR_PRIVATE_ROOT = str(tmp_path / "different-web-instance")
    assert storage.read_path(key, "f_0_0_0.jpg").read_bytes() == b"synthetic tile"
    with pytest.raises(TourError):
        storage.read_path(key, "../other.jpg")


def test_remote_cleanup_is_prefix_and_reference_scoped(settings, bucket):
    keep, orphan = "a" * 32, "b" * 32
    bucket.objects = {
        remote_storage.object_key(keep): b"keep",
        remote_storage.object_key(orphan): b"orphan",
        "test-tour-prefix/unrelated-document.txt": b"unrelated",
        "other-prefix/" + "c" * 32: b"other feature",
    }
    assert (
        remote_storage.sweep({keep}, (timezone.now() - timedelta(days=7)).timestamp())
        == 1
    )
    assert bucket.deleted == [remote_storage.object_key(orphan)]
    settings.VIRTUAL_TOUR_S3_PREFIX = ""
    with pytest.raises(TourError):
        remote_storage.sweep(set(), timezone.now().timestamp())
