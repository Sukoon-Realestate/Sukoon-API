"""Real direct/group transport parity, without a Celery worker or mocked media."""

import io
import shutil
import subprocess
import uuid
from datetime import timedelta
from unittest.mock import patch
import pytest
from PIL import Image
from channels.db import database_sync_to_async
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient
from core_apps.common.testing import WebsocketCommunicator
from core_apps.chat.consumers import ChatConsumer
from core_apps.chat.models import ChatEvent, ChatNotificationDelivery, Message
from core_apps.chat.services.message_service import (
    get_or_create_direct_conversation,
    send_message,
)
from core_apps.chat.services.direct_access import authorize
from core_apps.chat.services.group_typing import typing_payload
from core_apps.features.planning_models import RoommateConnection
from .conftest import message_request


@pytest.fixture
def direct_chat(user, another_user, settings, tmp_path):
    settings.CHAT_PRIVATE_MEDIA_ROOT = tmp_path / "private"
    for person in (user, another_user):
        person.is_verified = True
        person.save(update_fields=["is_verified"])
    return (
        get_or_create_direct_conversation(user=user, other_user=another_user),
        user,
        another_user,
    )


@pytest.mark.django_db
def test_direct_history_upgrade_read_only_consent_and_unrelated_actor(
    direct_chat, superuser
):
    conversation, user, other = direct_chat
    # Reproduce pre-workspace history, before rich chat prepared participants.
    conversation.participant_set.update(membership_period=None)
    old = Message.objects.create(
        conversation=conversation, sender=user, content="Original text"
    )
    client = APIClient()
    client.force_authenticate(user)
    base = f"/api/v1/chat/conversations/{conversation.id}/"
    response = client.get(base + "chat/")
    assert response.status_code == 200, response.content
    summary = response.json()["data"]
    old.refresh_from_db()
    assert old.sequence == 1
    assert summary["conversation_type"] == "direct"
    assert summary["group_id"] is None and summary["can_send"] is True
    assert "delete_any_message" not in summary["allowed_actions"]
    assert (
        client.get(base + "chat/").json()["data"]["membership_period"]
        == summary["membership_period"]
    )
    history = client.get(base + "messages/", {"protocol": "chat.v1"})
    assert history.status_code == 200
    assert history["X-Chat-Event-Cursor"]
    assert history.json()["data"][0]["id"] == str(old.id)
    first, second = sorted([user.pk, other.pk])
    RoommateConnection.objects.create(
        first_id=first, second_id=second, requester=user, status="withdrawn"
    )
    assert client.get(base + "chat/").json()["data"]["can_send"] is False
    assert client.get(base + "messages/", {"protocol": "chat.v1"}).status_code == 200
    assert (
        client.post(
            base + "messages/create/", message_request("Blocked"), format="json"
        ).status_code
        == 403
    )
    client.force_authenticate(superuser)
    for suffix in (
        "chat/",
        "messages/?protocol=chat.v1",
        "events/?after_cursor=" + summary["event_cursor"],
    ):
        assert client.get(base + suffix).status_code == 403


@pytest.mark.django_db
def test_queued_typing_is_suppressed_after_consent_withdrawal(direct_chat):
    conversation, user, other = direct_chat
    _, participant, _ = authorize(conversation, user)
    event = {
        "conversation_id": str(conversation.id),
        "actor_id": str(user.id),
        "membership_period": str(participant.membership_period),
        "started": True,
        "expires_at": (timezone.now() + timedelta(seconds=5)).isoformat(),
    }
    assert typing_payload(event, other)["type"] == "typing.started"
    first, second = sorted([user.pk, other.pk])
    RoommateConnection.objects.create(
        first_id=first, second_id=second, requester=user, status="withdrawn"
    )
    assert typing_payload(event, other) is None
    # Withdrawal retains legitimate history; it does not retain live presence.
    assert authorize(conversation, other)[2].can_send is False


@pytest.mark.django_db
def test_legacy_and_rich_direct_retry_share_one_identity(direct_chat):
    conversation, user, _ = direct_chat
    identity = uuid.uuid4()
    legacy = send_message(
        conversation=conversation,
        sender=user,
        content="Same operation",
        client_message_id=identity,
    )
    client = APIClient()
    client.force_authenticate(user)
    url = f"/api/v1/chat/conversations/{conversation.id}/messages/create/"
    response = client.post(
        url,
        message_request("Same operation", client_message_id=str(identity)),
        format="json",
    )
    assert response.status_code == 201, response.content
    assert response.json()["data"]["id"] == str(legacy.id)
    assert Message.objects.filter(conversation=conversation).count() == 1
    assert (
        client.post(
            url,
            message_request("Changed", client_message_id=str(identity)),
            format="json",
        ).status_code
        == 409
    )


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("kind", ["image", "voice"])
async def test_direct_private_media_broadcast_replay_and_download(
    direct_chat, kind, tmp_path, superuser
):
    conversation, user, other = direct_chat
    if kind == "image":
        output = io.BytesIO()
        Image.new("RGB", (120, 80), "blue").save(output, "JPEG")
        body = output.getvalue()
    else:
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            pytest.skip("Native AAC inspection requires ffmpeg and ffprobe")
        path = tmp_path / "voice.m4a"
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=44100",
                "-t",
                "2",
                "-c:a",
                "aac",
                str(path),
            ],
            check=True,
        )
        body = path.read_bytes()
    base = f"/api/v1/chat/conversations/{conversation.id}/"
    upload_id = str(uuid.uuid4())

    @database_sync_to_async
    def upload():
        client = APIClient()
        client.force_authenticate(user)
        response = client.post(
            base + "attachments/",
            {
                "client_upload_id": upload_id,
                "kind": kind,
                "file": SimpleUploadedFile("capture", body),
            },
            format="multipart",
        )
        assert response.status_code == 201, response.content
        item = response.json()["data"]
        client.force_authenticate(other)
        assert (
            client.get(base + f"attachments/{item['id']}/content/").status_code == 404
        )
        return item

    attachment = await upload()
    sockets = []
    try:
        for actor in (user, other):
            socket = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
            socket.scope["user"] = actor
            assert (await socket.connect())[0]
            sockets.append(socket)
        intent = message_request(
            "Photo caption" if kind == "image" else "",
            kind=kind,
            attachment_ids=[attachment["id"]],
        )
        packet = {
            "type": "message.send",
            "protocol": "chat.v1",
            "conversation_id": str(conversation.id),
            **intent,
        }
        await sockets[0].send_json_to(packet)
        sent = [await sockets[0].receive_json_from() for _ in range(2)]
        ack = next(event for event in sent if event["type"] == "message.ack")["payload"]
        received = await sockets[1].receive_json_from()
        assert received["payload"]["id"] == ack["id"]
        assert received["payload"]["kind"] == kind
        assert received["payload"]["attachments"][0]["id"] == attachment["id"]
        await sockets[0].send_json_to(packet)
        assert (await sockets[0].receive_json_from())["payload"]["id"] == ack["id"]
        assert await sockets[1].receive_nothing(timeout=0.1)

        @database_sync_to_async
        def download_and_authority():
            client = APIClient()
            client.force_authenticate(other)
            path = base + f"attachments/{attachment['id']}/content/"
            response = client.get(path)
            assert response.status_code == 200
            assert response["Cache-Control"] == "private, no-store"
            downloaded = b"".join(response.streaming_content)
            assert downloaded
            if kind == "image":
                assert Image.open(io.BytesIO(downloaded)).size == (120, 80)
            else:
                assert 1900 <= attachment["duration_ms"] <= 2100
                assert response["Content-Type"] == "audio/mp4"
            assert client.delete(base + f"messages/{ack['id']}/").status_code == 403
            client.force_authenticate(superuser)
            assert client.get(path).status_code == 403
            assert Message.objects.filter(conversation=conversation).count() == 1
            assert (
                ChatEvent.objects.filter(
                    conversation=conversation, kind="message.new"
                ).count()
                == 1
            )
            client.force_authenticate(user)
            assert client.delete(base + f"messages/{ack['id']}/").status_code == 200
            conversation.refresh_from_db()
            assert conversation.last_message_preview == ""
            assert conversation.participant_set.get(user=other).unread_count == 0
            client.force_authenticate(other)
            assert client.get(path).status_code == 404

        await download_and_authority()
    finally:
        for socket in sockets:
            await socket.disconnect()


@pytest.mark.django_db(transaction=True)
def test_legacy_socket_and_rich_direct_send_race_keeps_one_message(direct_chat):
    from .test_group_concurrency import race
    from core_apps.chat.services.group_send import send_group_message

    conversation, user, other = direct_chat
    identity = uuid.uuid4()
    payload = message_request("Concurrent original", client_message_id=str(identity))
    ids = race(
        lambda: send_message(
            conversation=conversation,
            sender=user,
            content=payload["content"],
            client_message_id=identity,
        ).id,
        lambda: send_group_message(conversation, user, payload).id,
    )
    assert ids[0] == ids[1]
    assert conversation.messages.count() == 1
    assert conversation.participant_set.get(user=other).unread_count == 1
    assert (
        ChatEvent.objects.filter(conversation=conversation, kind="message.new").count()
        == 1
    )


@pytest.mark.django_db(transaction=True)
def test_direct_push_keeps_post_commit_delivery_and_worker_deduplication(direct_chat):
    from core_apps.chat.services.group_outbox import deliver_pushes
    from core_apps.chat.services.group_send import send_group_message
    from core_apps.notifications.models import DeviceToken, PushDelivery
    from core_apps.notifications.services.push_delivery import dispatch

    conversation, user, other = direct_chat
    device = DeviceToken.objects.create(user=other, token="direct-queue-device")
    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device", return_value=True
    ) as push:
        message = send_group_message(conversation, user, message_request())
        push.assert_not_called()
        assert PushDelivery.objects.filter(notification__data__message_id=str(message.id)).count() == 1
        assert ChatNotificationDelivery.objects.get(event__message=message, user=other).push_claimed_at is not None
        deliver_pushes()
        assert dispatch() == 1
        assert dispatch() == 0
        push.assert_called_once()
        assert push.call_args.kwargs["token"] == device.token
