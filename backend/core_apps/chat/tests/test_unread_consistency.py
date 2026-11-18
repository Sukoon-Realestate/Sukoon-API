"""Inbox badges and filters follow visible incoming messages, not legacy counters."""

import pytest
from types import SimpleNamespace
from uuid import uuid4
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient
from core_apps.chat.models import (
    Conversation,
    ConversationParticipant,
    ConversationWorkspace,
    Message,
)
from core_apps.chat.serializers.conversation import ConversationSerializer
from core_apps.chat.services.conversation_preferences import update_preferences
from core_apps.chat.services.group_access import total_unread_count
from core_apps.chat.services.group_operations import mark_group_read
from core_apps.chat.services.group_projection import summary
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.inbox_preferences import organize_inbox
from core_apps.profiles.services.mvp_counts import active_counts
from .conftest import message_request
from . import test_direct_media
from .test_inbox_receipts import card

direct_chat = test_direct_media.direct_chat
pytestmark = pytest.mark.django_db


def assert_unread(conversation, reader, expected, *, legacy=False):
    ConversationWorkspace.objects.get_or_create(
        conversation=conversation, user=reader, workspace="individual"
    )
    assert card(conversation, reader)["unread_count"] == expected
    if not legacy:
        assert summary(conversation, reader)["unread_count"] == expected
    assert total_unread_count(reader) == expected
    assert active_counts(reader, "individual")["unread_chat_messages_count"] == expected
    client = APIClient()
    client.force_authenticate(reader)
    response = client.get(
        "/api/v1/features/v1/workspace-summary/", {"scope": "individual"}
    )
    assert response.status_code == 200
    assert response.data["workspace_chat_counts"]["individual"] == expected
    assert response.data["unread_chat_messages_count"] == expected
    assert organize_inbox(
        Conversation.objects.filter(pk=conversation.pk), reader, unread_only=True
    ).exists() == bool(expected)


def test_read_conversation_ignores_stale_counter(direct_chat):
    conversation, sender, reader = direct_chat
    message = send_group_message(conversation, sender, message_request("Already read"))
    mark_group_read(conversation, reader, message.sequence)
    conversation.participant_set.filter(user=reader).update(unread_count=43)
    assert_unread(conversation, reader, 0)


def test_partial_read_keeps_only_newer_incoming_messages(direct_chat):
    conversation, sender, reader = direct_chat
    first = send_group_message(conversation, sender, message_request("Read first"))
    send_group_message(conversation, sender, message_request("Still unread"))
    send_group_message(conversation, reader, message_request("Own outgoing"))
    deleted = send_group_message(conversation, sender, message_request("Deleted"))
    Message.objects.filter(pk=deleted.pk).update(deleted_at=timezone.now())
    mark_group_read(conversation, reader, first.sequence)
    conversation.participant_set.filter(user=reader).update(unread_count=43)
    assert_unread(conversation, reader, 1)


def test_legacy_unsequenced_messages_use_read_timestamp_and_visibility(direct_chat):
    conversation, sender, reader = direct_chat
    Message.objects.create(conversation=conversation, sender=sender, content="Legacy")
    conversation.participant_set.filter(user=reader).update(unread_count=43)
    assert_unread(conversation, reader, 1, legacy=True)
    conversation.participant_set.filter(user=reader).update(last_read_at=timezone.now())
    assert_unread(conversation, reader, 0, legacy=True)
    conversation.participant_set.filter(user=reader).update(
        last_read_at=None, visible_from_sequence=2
    )
    assert_unread(conversation, reader, 0, legacy=True)


def test_repeated_read_repairs_legacy_counter_without_advancing_receipt(direct_chat):
    conversation, sender, reader = direct_chat
    message = send_group_message(conversation, sender, message_request("Read once"))
    mark_group_read(conversation, reader, message.sequence)
    participant = conversation.participant_set.get(user=reader)
    read_at = participant.last_read_at
    conversation.participant_set.filter(user=reader).update(unread_count=43)
    result = mark_group_read(conversation, reader, message.sequence)
    participant.refresh_from_db()
    assert result["unread_count"] == participant.unread_count == 0
    assert participant.last_read_at == read_at


def test_manual_unread_reminder_stays_private_without_inflating_count(direct_chat):
    conversation, sender, reader = direct_chat
    message = send_group_message(conversation, sender, message_request("Read"))
    mark_group_read(conversation, reader, message.sequence)
    conversation.participant_set.filter(user=reader).update(unread_count=43)
    update_preferences(conversation, reader, {"is_marked_unread": True})
    assert card(conversation, reader)["unread_count"] == 0
    assert card(conversation, reader)["is_marked_unread"] is True
    assert card(conversation, sender)["is_marked_unread"] is False
    assert organize_inbox(
        Conversation.objects.filter(pk=conversation.pk), reader, unread_only=True
    ).exists()
    assert total_unread_count(reader) == 0
    mark_group_read(conversation, reader, message.sequence)
    assert_unread(conversation, reader, 0)


def test_prepared_inbox_counts_are_correct_without_per_card_queries(direct_chat):
    _, sender, reader = direct_chat
    chats = Conversation.objects.bulk_create([Conversation() for _ in range(20)])
    ConversationParticipant.objects.bulk_create(
        [
            ConversationParticipant(
                conversation=chat,
                user=person,
                membership_period=uuid4(),
                unread_count=43,
            )
            for chat in chats
            for person in (sender, reader)
        ]
    )
    Message.objects.bulk_create(
        [
            Message(conversation=chat, sender=sender, sequence=1, content="Unread")
            for chat in chats
        ]
    )
    query_counts = []
    for size in (1, 20):
        rows = list(Conversation.objects.filter(pk__in=[c.pk for c in chats[:size]]))
        with CaptureQueriesContext(connection) as queries:
            cards = ConversationSerializer(
                rows, many=True, context={"request": SimpleNamespace(user=reader)}
            ).data
        assert len(cards) == size
        assert all(row["unread_count"] == 1 for row in cards)
        query_counts.append(len(queries))
    assert query_counts[1] <= query_counts[0] + 1
