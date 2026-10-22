import hashlib
import io
import json
import shutil
import subprocess
import uuid
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient
from core_apps.chat.models import ChatAttachment, Message
from core_apps.chat.services.group_send import normalize_request
from core_apps.chat.services.rich_media import validate_waveform, voice_waveform
from .test_direct_media import direct_chat
from .test_group_media_remote import durable

pytestmark = pytest.mark.django_db


def test_legacy_upload_writer_survives_rich_media_migration(direct_chat):
    if connection.vendor != "postgresql":
        pytest.skip("Production rolling deployment uses PostgreSQL")
    legacy_apps = MigrationExecutor(connection).loader.project_state(
        [("chat", "0013_chatmoderationcase_notification_and_more")]
    ).apps
    legacy_attachment = legacy_apps.get_model("chat", "ChatAttachment")
    conversation, sender, _ = direct_chat
    old = legacy_attachment.objects.create(
        conversation_id=conversation.pk,
        uploader_id=sender.pk,
        membership_period=uuid.uuid4(),
        client_upload_id=uuid.uuid4(),
        kind="image",
        state="ready",
        fingerprint="a" * 64,
        storage_key="legacy-rolling-test.jpg",
        thumbnail_key="",
        mime_type="image/jpeg",
        byte_size=1,
    )
    current = ChatAttachment.objects.get(pk=old.pk)
    assert current.original_name == ""
    assert current.waveform == []


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def upload(client, base, name, content, kind="file", identity=None, **extra):
    return client.post(
        base + "attachments/",
        {
            "file": SimpleUploadedFile(name, content),
            "client_upload_id": str(identity or uuid.uuid4()),
            "kind": kind,
            "sha256": hashlib.sha256(content).hexdigest(),
            **extra,
        },
        format="multipart",
    )


@pytest.mark.parametrize(
    "name,content",
    [
        ("عقد الإيجار.pdf", b"%PDF-1.7\ncontract\n%%EOF"),
        ("records.csv", b"name,amount\nRental,2500"),
        ("archive.zip", b"PK\x03\x04opaque archive bytes"),
        ("custom.unrecognized", bytes(range(256))),
    ],
)
def test_arbitrary_files_are_private_named_downloads(
    direct_chat, durable, superuser, name, content
):
    conversation, sender, recipient = direct_chat
    base = f"/api/v1/chat/conversations/{conversation.id}/"
    client = client_for(sender)
    identity = uuid.uuid4()
    response = upload(client, base, name, content, identity=identity)
    assert response.status_code == 201, response.content
    attachment = response.json()["data"]
    assert attachment["original_name"] == name
    assert attachment["mime_type"] == "application/octet-stream"
    assert (
        upload(client, base, name, content, identity=identity).json()["data"]["id"]
        == attachment["id"]
    )
    assert (
        upload(
            client, base, "different-name.bin", content, identity=identity
        ).status_code
        == 409
    )
    payload = {
        "client_message_id": str(uuid.uuid4()),
        "kind": "file",
        "content": "Housing document",
        "attachment_ids": [attachment["id"]],
    }
    sent = client.post(base + "messages/create/", payload, format="json")
    assert sent.status_code == 201, sent.content
    assert (
        client.post(base + "messages/create/", payload, format="json").json()["data"][
            "id"
        ]
        == sent.json()["data"]["id"]
    )
    path = "/api/v1/" + attachment["content_path"]
    downloaded = client_for(recipient).get(path)
    assert downloaded.status_code == 200
    assert b"".join(downloaded.streaming_content) == content
    assert downloaded["Content-Disposition"].startswith("attachment;")
    assert downloaded["X-Content-Type-Options"] == "nosniff"
    assert downloaded["Cache-Control"] == "private, no-store"
    assert client_for(superuser).get(path).status_code == 403
    message = Message.objects.get(id=sent.json()["data"]["id"])
    message.deleted_at = timezone.now()
    message.save(update_fields=["deleted_at"])
    assert client_for(recipient).get(path).status_code == 404


def test_file_size_limit_and_empty_file(direct_chat, settings):
    conversation, sender, _ = direct_chat
    base = f"/api/v1/chat/conversations/{conversation.id}/"
    settings.CHAT_MEDIA_LIMITS = {"file_max_bytes": 16}
    client = client_for(sender)
    assert upload(client, base, "empty.pdf", b"").status_code == 400
    assert upload(client, base, "large.pdf", b"x" * 17).status_code == 400
    assert not ChatAttachment.objects.filter(conversation=conversation).exists()


def test_location_roundtrip_replay_and_deleted_projection(direct_chat):
    conversation, sender, recipient = direct_chat
    base = f"/api/v1/chat/conversations/{conversation.id}/"
    client = client_for(sender)
    assert {"file", "video", "location"} <= set(
        client.get(base + "chat/").json()["data"]["limits"]["message_kinds"]
    )
    payload = {
        "client_message_id": str(uuid.uuid4()),
        "kind": "location",
        "content": "",
        "location": {"latitude": 30.0444, "longitude": 31.2357, "accuracy_m": 12.0},
    }
    response = client.post(base + "messages/create/", payload, format="json")
    assert response.status_code == 201, response.content
    message = response.json()["data"]
    assert message["location"] == payload["location"]
    assert (
        client.post(base + "messages/create/", payload, format="json").json()["data"][
            "id"
        ]
        == message["id"]
    )
    changed = {**payload, "location": {**payload["location"], "latitude": 31}}
    assert (
        client.post(base + "messages/create/", changed, format="json").status_code
        == 409
    )
    history = (
        client_for(recipient)
        .get(base + "messages/", {"protocol": "chat.v1"})
        .json()["data"]
    )
    assert history[0]["location"] == payload["location"]
    row = Message.objects.get(id=message["id"])
    row.deleted_at = timezone.now()
    row.save(update_fields=["deleted_at"])
    history = (
        client_for(recipient)
        .get(base + "messages/", {"protocol": "chat.v1"})
        .json()["data"]
    )
    assert history[0]["location"] is None


@pytest.mark.parametrize(
    "location",
    [
        None,
        {},
        {"latitude": 91, "longitude": 0},
        {"latitude": True, "longitude": 1},
        {"latitude": float("nan"), "longitude": 1},
        {"latitude": 1, "longitude": 1, "accuracy_m": -1},
        {"latitude": 1, "longitude": 1, "url": "https://invalid"},
    ],
)
def test_invalid_coordinates_never_become_a_message(location):
    with pytest.raises(ValidationError):
        normalize_request(
            {
                "client_message_id": str(uuid.uuid4()),
                "kind": "location",
                "location": location,
            }
        )


@pytest.mark.parametrize(
    "value", [[float("nan")], [2], [-0.1], [True], [0] * 97, "waveform"]
)
def test_invalid_waveforms_are_rejected(value):
    with pytest.raises(ValidationError):
        validate_waveform(value)


def generate_media(path, video=False):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("Real FFmpeg and FFprobe are required")
    command = ["ffmpeg", "-v", "error", "-f", "lavfi"]
    command += (
        ["-i", "color=c=green:s=160x120:r=15", "-c:v", "libx264", "-pix_fmt", "yuv420p"]
        if video
        else ["-i", "sine=frequency=440:sample_rate=44100", "-c:a", "aac"]
    )
    subprocess.run([*command, "-t", "2", str(path)], check=True, capture_output=True)
    return path.read_bytes()


def test_voice_waveform_survives_upload_and_history(direct_chat, tmp_path):
    conversation, sender, recipient = direct_chat
    base = f"/api/v1/chat/conversations/{conversation.id}/"
    content = generate_media(tmp_path / "voice.m4a")
    levels = [0.1, 0.7, 0.4, 0.9, 0.2]
    client = client_for(sender)
    response = upload(
        client, base, "voice.m4a", content, kind="voice", waveform=json.dumps(levels)
    )
    assert response.status_code == 201, response.content
    attachment = response.json()["data"]
    assert attachment["waveform"] == levels
    response = client.post(
        base + "messages/create/",
        {
            "client_message_id": str(uuid.uuid4()),
            "kind": "voice",
            "attachment_ids": [attachment["id"]],
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    history = (
        client_for(recipient)
        .get(base + "messages/", {"protocol": "chat.v1"})
        .json()["data"]
    )
    assert history[0]["attachments"][0]["waveform"] == levels
    derived = voice_waveform(tmp_path / "voice.m4a")
    assert len(derived) == 96 and max(derived) > 0


def test_real_video_thumbnail_and_message(direct_chat, durable, tmp_path):
    conversation, sender, recipient = direct_chat
    base = f"/api/v1/chat/conversations/{conversation.id}/"
    content = generate_media(tmp_path / "video.mp4", video=True)
    client = client_for(sender)
    response = upload(client, base, "viewing.mp4", content, kind="video")
    assert response.status_code == 201, response.content
    attachment = response.json()["data"]
    assert attachment["mime_type"] == "video/mp4" and attachment["duration_ms"] == 2000
    assert attachment["width"] == 160 and attachment["thumbnail_path"]
    sent = client.post(
        base + "messages/create/",
        {
            "client_message_id": str(uuid.uuid4()),
            "kind": "video",
            "attachment_ids": [attachment["id"]],
        },
        format="json",
    )
    assert sent.status_code == 201, sent.content
    thumbnail = client_for(recipient).get("/api/v1/" + attachment["thumbnail_path"])
    assert thumbnail.status_code == 200
    from PIL import Image

    assert (
        Image.open(io.BytesIO(b"".join(thumbnail.streaming_content))).format == "JPEG"
    )
    assert (
        upload(client, base, "spoof.mp4", b"not a video", kind="video").status_code
        == 400
    )


@pytest.mark.parametrize("kind,size", [("file", 100), ("video", 11 * 1024 * 1024)])
def test_unsupported_provider_media_stays_uncertain_without_external_upload(kind, size):
    from types import SimpleNamespace
    from unittest.mock import patch
    from core_apps.chat.moderation.provider import GeminiReviewer

    with patch("core_apps.chat.moderation.provider.requests.post") as request:
        result = GeminiReviewer().extract(SimpleNamespace(kind=kind, byte_size=size))
    assert result == {"text": "", "uncertain": True}
    request.assert_not_called()
