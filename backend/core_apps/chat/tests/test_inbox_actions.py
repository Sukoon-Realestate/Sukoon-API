import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from core_apps.chat.models import (
    Conversation,
    ChatEvent,
    ChatNotificationDelivery,
    Message,
)
from core_apps.chat.services.conversation_preferences import (
    update_preferences,
    preferences_payload,
)
from core_apps.chat.services.inbox_preferences import (
    organize_inbox,
    notifications_muted,
)
from core_apps.chat.services.group_operations import mark_group_read
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.group_outbox import _notify
from core_apps.notifications.services.fcm_service import FCMService
from .conftest import message_request
from .test_forwarding import target_group

pytestmark = pytest.mark.django_db


def notification(conversation, owner, peer):
    message = send_group_message(conversation, owner, message_request())
    event = ChatEvent.objects.get(message=message, kind="message.new")
    _notify(event, peer)
    return ChatNotificationDelivery.objects.get(event=event, user=peer)


def action_body(delivery, action="reply"):
    return {
        "notification_id": str(delivery.notification.id),
        "recipient_id": str(delivery.user.id),
        "membership_period": delivery.notification.data["membership_period"],
        "action": action,
        "client_message_id": str(uuid.uuid4()),
        "content": "A reply from the notification",
    }


def test_personal_unread_does_not_reverse_receipts(chat_group):
    _, c, owner, peer = chat_group
    message = send_group_message(c, owner, message_request())
    mark_group_read(c, peer, message.sequence)
    before = c.participant_set.get(user=peer)
    update_preferences(c, peer, {"is_marked_unread": True})
    after = c.participant_set.get(user=peer)
    assert after.last_read_sequence == before.last_read_sequence
    assert after.last_read_at == before.last_read_at
    assert preferences_payload(c, peer)["is_marked_unread"]
    assert not preferences_payload(c, owner)["is_marked_unread"]
    assert list(
        organize_inbox(Conversation.objects.filter(id=c.id), peer, unread_only=True)
    ) == [c]
    mark_group_read(c, peer, message.sequence)
    assert not organize_inbox(
        Conversation.objects.filter(id=c.id), peer, unread_only=True
    ).exists()


def test_reading_older_notification_keeps_newer_reminder_and_unread(chat_group):
    _, c, owner, peer = chat_group
    first = send_group_message(c, owner, message_request())
    second = send_group_message(c, owner, message_request())
    update_preferences(c, peer, {"is_marked_unread": True})
    mark_group_read(c, peer, first.sequence)
    assert preferences_payload(c, peer)["is_marked_unread"]
    assert organize_inbox(
        Conversation.objects.filter(id=c.id), peer, unread_only=True
    ).exists()
    mark_group_read(c, peer, second.sequence)
    assert not organize_inbox(
        Conversation.objects.filter(id=c.id), peer, unread_only=True
    ).exists()


def test_pin_precedes_pagination_and_is_private(chat_group):
    _, first, owner, peer = chat_group
    second = target_group(owner, peer)
    send_group_message(first, owner, message_request("old"))
    send_group_message(second, owner, message_request("new"))
    update_preferences(first, peer, {"is_pinned": True})
    qs = Conversation.objects.filter(id__in=[first.id, second.id])
    assert list(organize_inbox(qs, peer)[:1]) == [first]
    assert list(organize_inbox(qs, owner)[:1]) == [second]
    client = APIClient()
    client.force_authenticate(peer)
    response = client.get(
        "/api/v1/chat/conversations/", {"workspace": "student", "page_size": 1}
    )
    assert response.status_code == 200
    assert response.data["results"][0]["id"] == str(first.id)
    assert response.data["results"][0]["is_pinned"]


@pytest.mark.parametrize(
    "duration,seconds", [("hour", 3600), ("day", 86400), ("week", 604800)]
)
def test_mute_expiration_is_authoritative(chat_group, duration, seconds):
    _, c, owner, peer = chat_group
    update_preferences(c, peer, {"mute_duration": duration})
    p = c.participant_set.get(user=peer)
    assert notifications_muted(p)
    assert seconds - 3 < (p.muted_until - timezone.now()).total_seconds() <= seconds
    p.muted_until = timezone.now() - timedelta(seconds=1)
    p.save()
    assert not preferences_payload(c, peer)["is_muted"]
    assert notification(c, owner, peer).notification_id
    update_preferences(c, peer, {"mute_duration": "forever"})
    p.refresh_from_db()
    assert p.is_muted and p.muted_until is None
    update_preferences(c, peer, {"mute_duration": "off"})
    assert not preferences_payload(c, peer)["is_muted"]


def test_notification_reply_idempotency_and_read_cutoff(chat_group):
    _, c, owner, peer = chat_group
    delivery = notification(c, owner, peer)
    latest = send_group_message(c, owner, message_request("arrived later"))
    client = APIClient()
    client.force_authenticate(peer)
    body = action_body(delivery)
    one = client.post(reverse("chat-notification-action"), body, format="json")
    two = client.post(reverse("chat-notification-action"), body, format="json")
    assert one.status_code == two.status_code == 200, one.data
    assert one.data["message_id"] == two.data["message_id"]
    assert (
        Message.objects.filter(client_message_id=body["client_message_id"]).count() == 1
    )
    assert (
        c.participant_set.get(user=peer).last_read_sequence
        == delivery.event.message.sequence
        < latest.sequence
    )
    delivery.notification.refresh_from_db()
    assert delivery.notification.is_read and delivery.notification.read_at


def test_notification_mark_read_sends_no_message(chat_group):
    _, c, owner, peer = chat_group
    delivery = notification(c, owner, peer)
    count = Message.objects.count()
    client = APIClient()
    client.force_authenticate(peer)
    response = client.post(
        reverse("chat-notification-action"),
        action_body(delivery, "mark_read"),
        format="json",
    )
    assert response.status_code == 200, response.data
    assert Message.objects.count() == count


@pytest.mark.parametrize("mismatch", ["recipient", "membership", "removed", "no_auth"])
def test_stale_or_foreign_notification_cannot_send(chat_group, mismatch):
    group, c, owner, peer = chat_group
    delivery = notification(c, owner, peer)
    client = APIClient()
    if mismatch != "no_auth":
        client.force_authenticate(peer if mismatch != "recipient" else owner)
    if mismatch == "membership":
        c.participant_set.filter(user=peer).update(membership_period=uuid.uuid4())
    if mismatch == "removed":
        group.memberships.filter(user=peer).update(status="removed")
    count = Message.objects.count()
    response = client.post(
        reverse("chat-notification-action"), action_body(delivery), format="json"
    )
    assert response.status_code in (401, 403), response.data
    assert Message.objects.count() == count


@pytest.mark.parametrize(
    "platform,version", [("android", 1), ("ios", 1), ("android", 0)]
)
def test_actions_push_is_versioned_and_private(platform, version):
    data = {
        "chat_actions_version": "1",
        "notification_id": str(uuid.uuid4()),
        "recipient_id": str(uuid.uuid4()),
        "membership_period": str(uuid.uuid4()),
        "conversation_id": str(uuid.uuid4()),
        "body": "private message",
    }
    with patch("requests.post", return_value=MagicMock(status_code=200)) as post:
        assert FCMService.send_push_to_device(
            "fake-device",
            "private sender",
            "private message",
            data=data,
            credentials=MagicMock(valid=True, token="fake"),
            project_id="fake",
            device_type=platform,
            chat_actions_version=version,
        )
    message = post.call_args.kwargs["json"]["message"]
    assert "private message" not in str(message) and "private sender" not in str(
        message
    )
    assert message["data"]["recipient_id"] == data["recipient_id"]
    if platform == "android" and version == 1:
        assert (
            "notification" not in message and "notification" not in message["android"]
        )
    elif platform == "ios":
        assert message["apns"]["payload"]["aps"]["category"] == "SOKOUN_CHAT_ACTIONS"
    else:
        assert "notification" in message
