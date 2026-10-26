"""Retry only the delivery; message identity, inbox receipt and consent stay fixed."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from core_apps.chat.models import ChatEvent, ChatNotificationDelivery, Message
from core_apps.chat.services.group_outbox import _notify, deliver_pushes
from core_apps.chat.services.group_send import send_group_message
from core_apps.notifications.models import DeviceToken, Notification, PushDelivery
from core_apps.notifications.services.push_delivery import dispatch
from .conftest import message_request

pytestmark = pytest.mark.django_db
SEND = "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device"


def queued(chat_group):
    _, chat, owner, peer = chat_group
    device = DeviceToken.objects.create(
        user=peer, token="student-chat-device", device_type="android"
    )
    message = send_group_message(chat, owner, message_request())
    event = ChatEvent.objects.get(message=message, kind="message.new")
    _notify(event, peer)
    deliver_pushes(event_pk=event.pk)
    return message, event, device


def due():
    PushDelivery.objects.update(next_attempt_at=timezone.now() - timedelta(seconds=1))


def test_failed_device_attempt_retries_the_same_receipt_once(chat_group):
    message, event, _ = queued(chat_group)
    notice = Notification.objects.get(notification_type="new_message")
    with patch(SEND, side_effect=[False, True]) as provider:
        assert dispatch() == 0
        deliver_pushes(event_pk=event.pk)
        due()
        assert dispatch() == 1
        assert dispatch() == 0
    assert provider.call_count == 2
    assert {
        call.kwargs["data"]["notification_id"] for call in provider.call_args_list
    } == {str(notice.id)}
    assert {call.kwargs["data"]["message_id"] for call in provider.call_args_list} == {
        str(message.id)
    }
    assert (
        Message.objects.count()
        == Notification.objects.count()
        == PushDelivery.objects.count()
        == 1
    )
    assert notice.scope == "student"


@pytest.mark.parametrize("change", ["read", "muted", "deleted", "membership_removed"])
def test_retry_rechecks_current_message_and_recipient(chat_group, change):
    group, chat, _, peer = chat_group
    message, _, _ = queued(chat_group)
    with patch(SEND, return_value=False):
        dispatch()
    if change == "read":
        chat.participant_set.filter(user=peer).update(
            last_read_sequence=message.sequence
        )
    elif change == "muted":
        chat.participant_set.filter(user=peer).update(is_muted=True)
    elif change == "deleted":
        Message.objects.filter(pk=message.pk).update(deleted_at=timezone.now())
    else:
        group.memberships.filter(user=peer).update(status="removed")
    due()
    with patch(SEND) as provider:
        assert dispatch() == 0
        provider.assert_not_called()
    assert PushDelivery.objects.get().suppressed
    assert Message.objects.filter(pk=message.pk).exists()


def test_failure_of_one_device_does_not_abort_or_repeat_another(chat_group):
    _, _, _, peer = chat_group
    DeviceToken.objects.create(
        user=peer, token="second-student-device", device_type="ios"
    )
    queued(chat_group)
    with patch(
        SEND, side_effect=[RuntimeError("synthetic provider disconnect"), True]
    ) as provider:
        assert dispatch() == 1
    assert provider.call_count == 2
    assert PushDelivery.objects.filter(accepted_at__isnull=False).count() == 1
    failed = PushDelivery.objects.get(accepted_at__isnull=True)
    assert failed.claimed_until is None and failed.attempts == 1
    due()
    with patch(SEND, return_value=True) as provider:
        assert dispatch() == 1
        provider.assert_called_once()
        assert provider.call_args.kwargs["token"] == failed.device.token


def test_enqueue_failure_keeps_chat_receipt_unclaimed_for_recovery(chat_group):
    _, chat, owner, peer = chat_group
    DeviceToken.objects.create(user=peer, token="recover-chat-device")
    message = send_group_message(chat, owner, message_request())
    event = ChatEvent.objects.get(message=message)
    _notify(event, peer)
    with patch(
        "core_apps.notifications.services.push_delivery.queue_notification",
        side_effect=RuntimeError("queue unavailable"),
    ):
        with pytest.raises(RuntimeError):
            deliver_pushes(event_pk=event.pk)
    assert ChatNotificationDelivery.objects.get(event=event).push_claimed_at is None
    deliver_pushes(event_pk=event.pk)
    assert PushDelivery.objects.count() == 1
    assert Message.objects.count() == 1


def test_previous_claimed_notice_is_not_recreated_or_requeued(chat_group):
    _, chat, owner, peer = chat_group
    DeviceToken.objects.create(user=peer, token="old-claimed-device")
    message = send_group_message(chat, owner, message_request())
    event = ChatEvent.objects.get(message=message)
    _notify(event, peer)
    ChatNotificationDelivery.objects.filter(event=event).update(
        push_claimed_at=timezone.now()
    )
    deliver_pushes(event_pk=event.pk)
    assert not PushDelivery.objects.exists()
    assert Notification.objects.count() == Message.objects.count() == 1
