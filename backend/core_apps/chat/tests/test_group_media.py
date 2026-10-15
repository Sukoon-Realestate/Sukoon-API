import io
import shutil
import subprocess
import uuid
from datetime import timedelta
from unittest.mock import patch
import pytest
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from core_apps.chat.models import ChatAttachment
from core_apps.chat.services.group_limits import ChatConflict, ChatUnavailable
from core_apps.chat.services.group_media_storage import (
    cleanup_orphans,
    private_path,
    upload_attachment,
)
from core_apps.chat.services.group_operations import delete_group_message
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.views.group_attachments import accessible_attachment
from .conftest import message_request

pytestmark = pytest.mark.django_db


def image_file():
    data = io.BytesIO()
    Image.new("RGB", (100, 100), "red").save(data, "JPEG")
    return SimpleUploadedFile("forged.svg", data.getvalue(), content_type="text/plain")


def test_inspected_private_image_dedup_conflict_and_deleted_media(chat_group):
    _, conversation, user, member = chat_group
    identity = uuid.uuid4()
    image = upload_attachment(conversation, user, image_file(), identity, "image")
    assert image.mime_type == "image/jpeg" and image.width == 100
    assert (
        upload_attachment(conversation, user, image_file(), identity, "image").id
        == image.id
    )
    with pytest.raises(ChatConflict):
        upload_attachment(
            conversation, user, SimpleUploadedFile("x", b"different"), identity, "image"
        )
    with pytest.raises(NotFound):
        accessible_attachment(conversation, member, identity=image.id)
    message = send_group_message(
        conversation,
        user,
        message_request("Caption", kind="image", attachment_ids=[str(image.id)]),
    )
    assert (
        accessible_attachment(conversation, member, identity=image.id).message_id
        == message.pk
    )
    with pytest.raises(ValidationError):
        send_group_message(
            conversation,
            member,
            message_request(kind="image", attachment_ids=[str(image.id)]),
        )
    delete_group_message(conversation, user, message.id)
    with pytest.raises(NotFound):
        accessible_attachment(conversation, member, identity=image.id)
    cleanup_orphans()
    assert not private_path(image.storage_key).exists()
    assert not private_path(image.thumbnail_key).exists()
    with pytest.raises(ChatConflict):
        upload_attachment(conversation, user, image_file(), identity, "image")


@pytest.mark.parametrize("body", [b"<svg/>", b"broken", b""])
def test_corrupt_and_non_raster_uploads_rejected(chat_group, body):
    _, conversation, user, _ = chat_group
    with pytest.raises(ValidationError):
        upload_attachment(
            conversation, user, SimpleUploadedFile("x.jpg", body), uuid.uuid4(), "image"
        )
    assert not ChatAttachment.objects.exists()


def test_image_limits_and_bundle_authority(chat_group, settings):
    _, conversation, user, member = chat_group
    settings.CHAT_MEDIA_LIMITS = {"image_max_pixels": 500}
    with pytest.raises(ValidationError):
        upload_attachment(conversation, user, image_file(), uuid.uuid4(), "image")
    settings.CHAT_MEDIA_LIMITS = {"image_max_bytes": 10}
    with pytest.raises(ValidationError):
        upload_attachment(conversation, user, image_file(), uuid.uuid4(), "image")
    settings.CHAT_MEDIA_LIMITS = {}
    image = upload_attachment(conversation, user, image_file(), uuid.uuid4(), "image")
    for ids in [[str(image.id)] * 6, [str(image.id)]]:
        with pytest.raises(ValidationError):
            send_group_message(
                conversation, member, message_request(kind="image", attachment_ids=ids)
            )


def test_removed_during_validation_cannot_finalize(chat_group):
    from core_apps.chat.services.group_media_validation import inspect_image

    group, conversation, user, member = chat_group

    def remove_then_inspect(path):
        group.memberships.filter(user=member).update(status="removed")
        return inspect_image(path)

    with patch(
        "core_apps.chat.services.group_media_storage.inspect_image", remove_then_inspect
    ):
        with pytest.raises(PermissionDenied):
            upload_attachment(conversation, member, image_file(), uuid.uuid4(), "image")
    assert not ChatAttachment.objects.exists()


def test_orphan_cleanup_preserves_attached_and_is_idempotent(
    chat_group, django_capture_on_commit_callbacks
):
    _, conversation, user, _ = chat_group
    orphan = upload_attachment(conversation, user, image_file(), uuid.uuid4(), "image")
    attached = upload_attachment(
        conversation, user, image_file(), uuid.uuid4(), "image"
    )
    send_group_message(
        conversation,
        user,
        message_request(kind="image", attachment_ids=[str(attached.id)]),
    )
    ChatAttachment.objects.update(created_at=timezone.now() - timedelta(days=2))
    with django_capture_on_commit_callbacks(execute=True):
        assert cleanup_orphans() == 1
    assert not private_path(orphan.storage_key).exists()
    assert private_path(attached.storage_key).exists()
    assert cleanup_orphans() == 0


def test_storage_failure_is_not_success(chat_group):
    _, conversation, user, _ = chat_group
    with patch(
        "core_apps.chat.services.group_media_storage.private_root",
        side_effect=OSError("disk full"),
    ):
        with pytest.raises(ChatUnavailable):
            upload_attachment(conversation, user, image_file(), uuid.uuid4(), "image")
    assert not ChatAttachment.objects.exists()


def test_verified_voice_codec_duration_and_mime(chat_group, tmp_path, settings):
    executable = shutil.which("ffmpeg")
    if not executable or not shutil.which("ffprobe"):
        pytest.skip("Real ffmpeg/ffprobe required for media inspection evidence")
    _, conversation, user, _ = chat_group
    path = tmp_path / "fixture.m4a"
    subprocess.run(
        [
            executable,
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=mono",
            "-t",
            "2",
            "-c:a",
            "aac",
            str(path),
        ],
        check=True,
    )
    voice = upload_attachment(
        conversation,
        user,
        SimpleUploadedFile("voice.txt", path.read_bytes()),
        uuid.uuid4(),
        "voice",
    )
    assert voice.mime_type == "audio/mp4" and 1900 <= voice.duration_ms <= 2100
    settings.CHAT_MEDIA_LIMITS = {"voice_max_duration_ms": 1000}
    with pytest.raises(ValidationError):
        upload_attachment(
            conversation,
            user,
            SimpleUploadedFile("voice.m4a", path.read_bytes()),
            uuid.uuid4(),
            "voice",
        )
    with pytest.raises(ValidationError):
        upload_attachment(conversation, user, image_file(), uuid.uuid4(), "voice")
