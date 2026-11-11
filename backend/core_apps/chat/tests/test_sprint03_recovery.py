"""Sprint 03 receipts and connection-scoped presence regressions."""

import asyncio
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from channels.db import database_sync_to_async
from django.utils import timezone
from core_apps.chat.models import ChatPresenceLease, Message
from core_apps.chat.services.message_service import (
    send_message,
    get_or_create_direct_conversation,
    ChatMessageConflict,
)
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.group_limits import ChatConflict
from core_apps.chat.services.message_mutations import mutate_message
from core_apps.chat.services.group_operations import delete_group_message
from core_apps.chat.services.presence import set_user_online_status, is_user_online
from .test_message_mutations import packet
from .test_consumers import _build_communicator


@pytest.mark.django_db
@pytest.mark.parametrize("historical", [False, "before_edit", "after_edit"])
def test_original_legacy_send_retries_after_edit_and_delete(user, another_user, historical):
    chat = get_or_create_direct_conversation(user=user, other_user=another_user)
    identity = uuid4()
    message = send_message(
        conversation=chat, sender=user, content="Original", client_message_id=identity
    )
    if historical == "before_edit":
        Message.objects.filter(pk=message.pk).update(payload_fingerprint="")
    mutate_message(chat, user, packet(chat, user, message))
    if historical == "after_edit":
        Message.objects.filter(pk=message.pk).update(payload_fingerprint="")
    assert (
        send_message(
            conversation=chat, sender=user, content="Original", client_message_id=identity
        ).content
        == "Corrected text"
    )
    rich = {"client_message_id": str(identity), "kind": "text", "content": "Original"}
    assert send_group_message(chat, user, rich).id == message.id
    delete_group_message(chat, user, message.id)
    retry = send_message(
        conversation=chat, sender=user, content="Original", client_message_id=identity
    )
    assert retry.id == message.id and retry.deleted_at and retry.content == ""
    assert send_group_message(chat, user, rich).deleted_at
    with pytest.raises(ChatMessageConflict):
        send_message(conversation=chat, sender=user, content="Changed", client_message_id=identity)
    with pytest.raises(ChatConflict):
        send_group_message(chat, user, {**rich, "content": "Changed"})
    assert Message.objects.filter(conversation=chat).count() == 1


@pytest.mark.django_db
def test_historical_delete_preserves_original_but_unrecoverable_tombstone_fails_closed(
    user, another_user
):
    chat = get_or_create_direct_conversation(user=user, other_user=another_user)
    identity = uuid4()
    message = send_message(
        conversation=chat, sender=user, content="Original", client_message_id=identity
    )
    Message.objects.filter(pk=message.pk).update(payload_fingerprint="")
    delete_group_message(chat, user, message.id)
    assert send_message(
        conversation=chat, sender=user, content="Original", client_message_id=identity
    ).deleted_at
    Message.objects.filter(pk=message.pk).update(payload_fingerprint="")
    with pytest.raises(ChatMessageConflict):
        send_message(conversation=chat, sender=user, content="Original", client_message_id=identity)


@pytest.mark.django_db
def test_presence_lease_renewal_disconnect_and_abandoned_expiry(user):
    now = timezone.now()
    with patch("django.utils.timezone.now", return_value=now):
        set_user_online_status(user.id, True, "tab-one")
        set_user_online_status(user.id, True, "tab-two")
        set_user_online_status(user.id, False, "tab-one")
        assert is_user_online(user.id)
    with patch("django.utils.timezone.now", return_value=now + timedelta(seconds=250)):
        set_user_online_status(user.id, True, "tab-two")
    with patch("django.utils.timezone.now", return_value=now + timedelta(seconds=301)):
        assert is_user_online(user.id)
    with patch("django.utils.timezone.now", return_value=now + timedelta(seconds=551)):
        assert not is_user_online(user.id)


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_socket_tabs_and_automatic_renewal(user, monkeypatch):
    import core_apps.chat.services.presence as presence

    monkeypatch.setattr(presence, "ONLINE_TTL_SECONDS", 0.3)
    first, second = _build_communicator(user), _build_communicator(user)
    try:
        assert (await first.connect())[0]
        assert (await second.connect())[0]
        await first.disconnect()
        await asyncio.sleep(0.45)
        assert await database_sync_to_async(is_user_online)(user.id)
        assert await database_sync_to_async(ChatPresenceLease.objects.count)() == 1
    finally:
        await second.disconnect()
    assert not await database_sync_to_async(is_user_online)(user.id)


@pytest.mark.django_db
def test_legacy_send_receipt_cannot_cross_cleared_history(user, another_user):
    chat = get_or_create_direct_conversation(user=user, other_user=another_user)
    identity = uuid4()
    message = send_message(
        conversation=chat, sender=user, content="Original", client_message_id=identity
    )
    chat.participant_set.filter(user=user).update(visible_from_sequence=message.sequence + 1)
    with pytest.raises(ChatMessageConflict):
        send_message(conversation=chat, sender=user, content="Original", client_message_id=identity)
    assert Message.objects.filter(conversation=chat).count() == 1


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_cancelled_socket_application_releases_presence(user):
    socket = _build_communicator(user)
    assert (await socket.connect())[0]
    # A response establishes that connect (including lease setup) completed.
    await socket.send_json_to({"type": "unknown"})
    assert (await socket.receive_json_from())["error"] == "Unknown message type."
    assert await database_sync_to_async(is_user_online)(user.id)
    socket.future.cancel()
    with pytest.raises(asyncio.CancelledError):
        await socket.future
    assert not await database_sync_to_async(is_user_online)(user.id)
