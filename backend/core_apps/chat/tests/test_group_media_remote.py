import hashlib
import json
import uuid
from unittest.mock import patch
import pytest
from django.core.management import call_command
from rest_framework.test import APIRequestFactory, force_authenticate
from core_apps.chat.models import ChatAttachment
from core_apps.chat.services import group_media_remote as remote
from core_apps.chat.services.group_limits import ChatUnavailable
from core_apps.chat.services.group_media_storage import (
    private_path,
    read_private_path,
    upload_attachment,
)
from core_apps.chat.views.group_attachments import GroupAttachmentDetailAPIView
from .test_group_media import image_file

pytestmark = pytest.mark.django_db


@pytest.fixture
def durable(settings):
    settings.CHAT_PRIVATE_STORAGE_PROVIDER = "cloudinary"
    settings.CHAT_CLOUDINARY_PREFIX = "chat-test"
    objects, calls = {}, []

    def upload(identity, content):
        assert identity.startswith("chat-test/")
        objects.setdefault(identity, content)
        calls.append(identity)

    def download(identity, maximum):
        body = objects[identity]
        assert len(body) <= maximum
        return body

    with patch.object(remote.cloud, "upload", side_effect=upload), patch.object(
        remote.cloud, "download", side_effect=download
    ):
        yield objects, calls


def test_acknowledged_image_and_thumbnail_survive_cache_loss(chat_group, durable):
    _, conversation, owner, _ = chat_group
    item = upload_attachment(conversation, owner, image_file(), uuid.uuid4(), "image")
    objects, calls = durable
    assert len(objects) == 4
    for key in (item.storage_key, item.thumbnail_key):
        file = private_path(key)
        expected = file.read_bytes()
        file.unlink()
        assert read_private_path(key).read_bytes() == expected
        assert read_private_path(key).stat().st_mode & 0o777 == 0o600
    assert len(calls) == 4


def test_chunked_attachment_roundtrip_and_manifest_last(chat_group, durable):
    key = uuid.uuid4().hex + ".m4a"
    source = private_path(key)
    data = b"x" * (remote.cloud.CHUNK_BYTES + 17)
    source.write_bytes(data)
    remote.persist(key, source)
    objects, calls = durable
    assert len(objects) == 3 and calls[-1].endswith("/manifest")
    source.unlink()
    assert read_private_path(key).read_bytes() == data


@pytest.mark.parametrize("extension", ["bin", "mp4"])
def test_rich_file_above_legacy_limit_survives_service_replacement(
    chat_group, durable, extension
):
    key = uuid.uuid4().hex + "." + extension
    source = private_path(key)
    data = b"x" * (12 * 1024 * 1024)
    source.write_bytes(data)
    remote.persist(key, source)
    remote.verify_backup(key, source)
    source.unlink()
    assert read_private_path(key).read_bytes() == data


@pytest.mark.parametrize(
    "extension,limit", [("bin", "file_max_bytes"), ("mp4", "video_max_bytes")]
)
def test_rich_remote_restore_enforces_its_own_kind_budget(
    chat_group, durable, settings, extension, limit
):
    settings.CHAT_MEDIA_LIMITS = {limit: 16}
    key = uuid.uuid4().hex + "." + extension
    source = private_path(key)
    source.write_bytes(b"x" * 17)
    remote.persist(key, source)
    source.unlink()
    with pytest.raises(ChatUnavailable):
        read_private_path(key)
    assert not source.exists()


def test_cloud_failure_never_acknowledges_local_only_upload(chat_group, durable):
    _, conversation, owner, _ = chat_group
    with patch.object(
        remote.cloud, "upload", side_effect=RuntimeError("SECRET_SIGNED_URL")
    ):
        with pytest.raises(ChatUnavailable) as error:
            upload_attachment(conversation, owner, image_file(), uuid.uuid4(), "image")
    assert "SECRET" not in str(error.value)
    assert not ChatAttachment.objects.exists()
    assert not list(private_path("placeholder").parent.iterdir())


def test_corrupt_remote_bytes_never_become_local_success(chat_group, durable):
    _, conversation, owner, _ = chat_group
    item = upload_attachment(conversation, owner, image_file(), uuid.uuid4(), "image")
    file = private_path(item.storage_key)
    file.unlink()
    objects, _ = durable
    key = next(
        k
        for k in objects
        if k.startswith("chat-test/" + item.storage_key[:32]) and "/part-" in k
    )
    objects[key] = b"corrupt"
    with pytest.raises(ChatUnavailable):
        read_private_path(item.storage_key)
    assert not file.exists()
    assert not list(file.parent.glob("*.pending"))


def test_unauthorized_download_never_materializes_private_bytes(chat_group, durable):
    _, conversation, owner, member = chat_group
    item = upload_attachment(conversation, owner, image_file(), uuid.uuid4(), "image")
    private_path(item.storage_key).unlink()
    request = APIRequestFactory().get("/")
    force_authenticate(request, member)
    with patch.object(remote.cloud, "download") as download:
        response = GroupAttachmentDetailAPIView.as_view()(
            request, id=conversation.id, attachment_id=item.id, content="content"
        )
    assert response.status_code == 404
    download.assert_not_called()


def test_legacy_backfill_verifies_remote_without_changing_identity(
    chat_group, durable, settings
):
    _, conversation, owner, _ = chat_group
    settings.CHAT_PRIVATE_STORAGE_PROVIDER = "local"
    item = upload_attachment(conversation, owner, image_file(), uuid.uuid4(), "image")
    settings.CHAT_PRIVATE_STORAGE_PROVIDER = "cloudinary"
    call_command("backfill_private_chat_media")
    item.refresh_from_db()
    assert item.state == "ready"
    for key in [item.storage_key, item.thumbnail_key]:
        expected = hashlib.sha256(private_path(key).read_bytes()).hexdigest()
        private_path(key).unlink()
        assert (
            hashlib.sha256(read_private_path(key).read_bytes()).hexdigest() == expected
        )


@pytest.mark.parametrize(
    "key", ["../private", "a" * 32 + ".png", "https://foreign.invalid/key"]
)
def test_foreign_keys_never_reach_provider(durable, key):
    with pytest.raises(ChatUnavailable):
        remote.identity(key)
    assert not durable[1]


def test_manifest_cannot_inflate_chat_file_budget(chat_group, durable):
    _, conversation, owner, _ = chat_group
    item = upload_attachment(conversation, owner, image_file(), uuid.uuid4(), "image")
    private_path(item.storage_key).unlink()
    objects, _ = durable
    manifest = "chat-test/" + item.storage_key[:32] + "/manifest"
    doc = json.loads(objects[manifest])
    doc["bytes"] = 200 * 1024**2
    objects[manifest] = json.dumps(doc).encode()
    with pytest.raises(ChatUnavailable):
        read_private_path(item.storage_key)


def test_remote_cleanup_is_scoped_to_revoked_attachment(chat_group, durable):
    from core_apps.chat.services.group_media_storage import remove_files

    _, conversation, owner, _ = chat_group
    item = upload_attachment(conversation, owner, image_file(), uuid.uuid4(), "image")
    other = upload_attachment(conversation, owner, image_file(), uuid.uuid4(), "image")
    objects, _ = durable

    def listed(**options):
        return {
            "resources": [
                {"public_id": k} for k in objects if k.startswith(options["prefix"])
            ]
        }

    def destroy(identity, **options):
        assert options == {"resource_type": "raw", "type": "authenticated"}
        objects.pop(identity, None)
        return {"result": "ok"}

    with patch.object(
        remote.cloud.cloudinary.api, "resources", side_effect=listed
    ), patch.object(remote.cloud.cloudinary.uploader, "destroy", side_effect=destroy):
        remove_files(item)
        assert len(objects) == 8  # Active references must never be destroyed.
        item.state = "revoked"
        item.save(update_fields=["state"])
        remove_files(item)
    assert len(objects) == 4
    assert all(
        other.storage_key[:32] in k or other.thumbnail_key[:32] in k for k in objects
    )


def test_shared_tour_namespace_is_rejected(chat_group, durable, settings):
    settings.CHAT_CLOUDINARY_PREFIX = settings.VIRTUAL_TOUR_CLOUDINARY_PREFIX
    with pytest.raises(ChatUnavailable):
        remote.identity(uuid.uuid4().hex + ".jpg")
