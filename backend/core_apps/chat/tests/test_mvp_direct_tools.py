"""MVP message tools exercised without provisioning a deferred housing group."""
from datetime import timedelta
from uuid import uuid4
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.exceptions import APIException
from rest_framework.test import APIClient

from core_apps.chat.models import ChatBlock, ChatEvent, MessagePin, MessageReadReceipt
from core_apps.chat.services.forward_batch import forward_batch
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.group_events import event_payload
from core_apps.chat.services.group_operations import delete_group_message, mark_group_read
from core_apps.chat.services.group_projection import message_payload, summary
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from core_apps.chat.services.message_tools import message_readers, reader_payload, set_message_tool
from .conftest import message_request
from .test_direct_media import direct_chat  # noqa: F401

pytestmark = pytest.mark.django_db


def command(conversation, user, **values):
    return {"membership_period": str(authorize(conversation, user)[1].membership_period),
            "operation_id": str(uuid4()), **values}


def project(conversation, user, message):
    _, participant, member = authorize(conversation, user)
    return message_payload(message, participant, member)


def batch(source, targets, user, messages):
    return {"operation_id": str(uuid4()),
            "source_membership_period": str(authorize(source, user)[1].membership_period),
            "messages": [{"id": str(m.id), "expected_revision": m.revision} for m in messages],
            "destinations": [{"id": str(t.id), "membership_period": str(authorize(t, user)[1].membership_period)}
                             for t in targets]}


def test_direct_star_is_private_and_retry_does_not_reverse_newer_choice(direct_chat):
    conversation, owner, peer = direct_chat
    message = send_group_message(conversation, owner, message_request("private bookmark"))
    first = command(conversation, peer, enabled=True)
    assert set_message_tool(conversation, peer, message.id, first)["is_starred"]
    event = ChatEvent.objects.get(kind="message.star")
    assert event_payload(event, owner) is None
    assert event_payload(event, peer)["payload"]["is_starred"]
    assert not project(conversation, owner, message)["is_starred"]
    set_message_tool(conversation, peer, message.id, command(conversation, peer, enabled=False))
    assert not set_message_tool(conversation, peer, message.id, first)["is_starred"]
    with pytest.raises(APIException):
        set_message_tool(conversation, peer, message.id, {**first, "enabled": False})


def test_direct_pin_is_shared_bounded_expires_and_rechecks_block(direct_chat):
    conversation, owner, peer = direct_chat
    messages = [send_group_message(conversation, owner, message_request(str(i))) for i in range(4)]
    for message in messages[:3]:
        set_message_tool(conversation, peer, message.id, command(conversation, peer, enabled=True), pin=True)
    assert len(summary(conversation, owner)["pinned_messages"]) == 3
    with pytest.raises(APIException):
        set_message_tool(conversation, owner, messages[3].id, command(conversation, owner, enabled=True), pin=True)
    MessagePin.objects.filter(message=messages[0]).update(expires_at=timezone.now() - timedelta(seconds=1))
    assert len(summary(conversation, owner)["pinned_messages"]) == 2
    set_message_tool(conversation, owner, messages[3].id, command(conversation, owner, enabled=True), pin=True)
    ChatBlock.objects.create(user=owner, blocked_user=peer)
    with pytest.raises(APIException):
        set_message_tool(conversation, peer, messages[3].id, command(conversation, peer, enabled=False), pin=True)


def test_direct_reply_keeps_exact_identity_and_redacts_deleted_original(direct_chat):
    conversation, owner, peer = direct_chat
    original = send_group_message(conversation, owner, message_request("original private text"))
    reply = send_group_message(conversation, peer, message_request("answer", reply_to_message_id=str(original.id)))
    assert reply.reply_to_id == original.pk
    assert project(conversation, owner, reply)["reply_to"]["id"] == str(original.id)
    delete_group_message(conversation, owner, original.id)
    reply.refresh_from_db()
    projected = project(conversation, peer, reply)
    assert "original private text" not in str(projected)
    assert projected["content"] == "answer"


def test_direct_first_read_time_is_stable_and_reader_details_are_sender_only(direct_chat):
    conversation, owner, peer = direct_chat
    first, second = [send_group_message(conversation, owner, message_request(str(i))) for i in range(2)]
    mark_group_read(conversation, peer, first.sequence)
    at = MessageReadReceipt.objects.get(message=first).read_at
    mark_group_read(conversation, peer, second.sequence)
    assert MessageReadReceipt.objects.get(message=first).read_at == at
    message, readers = message_readers(conversation, owner, first.id)
    assert reader_payload(message, readers.get())["read_at"] == at.isoformat()
    with pytest.raises(APIException):
        message_readers(conversation, peer, first.id)


def test_direct_forward_batch_orders_replays_and_does_not_duplicate_after_lost_ack(direct_chat, superuser):
    source, owner, peer = direct_chat
    superuser.is_verified = True
    superuser.save(update_fields=["is_verified"])
    target = get_or_create_direct_conversation(user=peer, other_user=superuser)
    messages = [send_group_message(source, owner, message_request(str(i))) for i in range(3)]
    request = batch(source, [target], peer, list(reversed(messages)))
    result = forward_batch(source, peer, request)
    assert list(target.messages.order_by("sequence").values_list("content", flat=True)) == ["0", "1", "2"]
    delete_group_message(source, owner, messages[0].id)
    assert forward_batch(source, peer, request) == result
    assert target.messages.count() == 3
    assert all(m.is_forwarded and m.reply_to_id is None for m in target.messages.all())
    client = APIClient()
    client.force_authenticate(owner)
    assert client.get(f"/api/v1/chat/conversations/{target.id}/messages/?protocol=chat.v1").status_code == 403
    with pytest.raises(APIException):
        forward_batch(source, peer, {**request, "messages": request["messages"][:1]})


def test_direct_forward_batch_rolls_back_every_destination_if_one_is_blocked(direct_chat, superuser):
    source, owner, peer = direct_chat
    superuser.is_verified = True
    superuser.save(update_fields=["is_verified"])
    targets = [get_or_create_direct_conversation(user=peer, other_user=superuser),
               get_or_create_direct_conversation(user=peer, other_user=owner, workspace="owner")]
    message = send_group_message(source, owner, message_request("send once or not at all"))
    request = batch(source, targets, peer, [message])
    # A destination loses authority after the composer prepared the request.
    ChatBlock.objects.create(user=superuser, blocked_user=peer)
    with pytest.raises(APIException):
        forward_batch(source, peer, request)
    assert all(not target.messages.exists() for target in targets)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('change', ['read', 'muted', 'deleted', 'blocked'])
def test_direct_push_retry_rechecks_message_and_recipient_without_resending(direct_chat, change):
    from core_apps.notifications.models import DeviceToken, Notification, PushDelivery
    from core_apps.notifications.services.push_delivery import dispatch

    conversation, owner, peer = direct_chat
    DeviceToken.objects.create(user=peer, token='synthetic-direct-retry-device')
    message = send_group_message(conversation, owner, message_request('queued once'))
    notice = Notification.objects.get(notification_type='new_message')
    assert PushDelivery.objects.filter(notification=notice).count() == 1
    provider = 'core_apps.notifications.services.fcm_service.FCMService.send_push_to_device'
    with patch(provider, return_value=False) as send:
        assert dispatch() == 0
        send.assert_called_once()
    if change == 'read':
        mark_group_read(conversation, peer, message.sequence)
    elif change == 'muted':
        conversation.participant_set.filter(user=peer).update(is_muted=True)
    elif change == 'deleted':
        delete_group_message(conversation, owner, message.id)
    else:
        ChatBlock.objects.create(user=owner, blocked_user=peer)
    PushDelivery.objects.update(next_attempt_at=timezone.now() - timedelta(seconds=1))
    with patch(provider) as send:
        assert dispatch() == 0
        send.assert_not_called()
    assert PushDelivery.objects.get(notification=notice).suppressed
    assert conversation.messages.count() == 1
    assert Notification.objects.filter(pk=notice.pk).count() == 1
