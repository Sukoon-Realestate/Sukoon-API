"""Prepared chat pages retain current membership and bound projection SQL/memory."""

from uuid import uuid4
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from core_apps.chat.models import Message, MessageReadReceipt
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.message_tools import record_reads
from core_apps.chat.views.group_history import history_response
from core_apps.admin_api.tests.test_sprint04_performance import measured

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("size", [1, 30, 100])
def test_chat_history_query_budget_and_fresh_membership(size, chat_group):
    group, conversation, owner, peer = chat_group
    Message.objects.bulk_create(
        [
            Message(
                conversation=conversation,
                sender=owner,
                sequence=i + 1,
                client_message_id=uuid4(),
                kind="text",
                content=f"Private {i}",
            )
            for i in range(size)
        ]
    )
    conversation.last_sequence = size
    conversation.save(update_fields=["last_sequence"])
    response, report = measured(
        "group-message-history",
        size,
        lambda: history_response(conversation, peer, {"limit": str(size)}).data,
    )
    assert len(response) == size
    assert all(
        row["eligible_reader_count"] == 1 and row["read_by_count"] == 0
        for row in response
    )
    assert report["queries"] <= 20
    group.memberships.filter(user=peer).update(status="removed")
    with pytest.raises(PermissionDenied):
        history_response(conversation, peer, {"limit": "100"})


def test_read_receipts_materialize_at_most_500_preserve_timestamp_and_retry(chat_group):
    _, conversation, owner, peer = chat_group
    Message.objects.bulk_create(
        [
            Message(
                conversation=conversation,
                sender=owner,
                sequence=i + 1,
                kind="text",
                content="Private",
            )
            for i in range(1201)
        ]
    )
    _, participant, _ = authorize(conversation, peer)
    read_at = timezone.now()
    original = MessageReadReceipt.objects.bulk_create
    sizes = []

    def create(rows, **kwargs):
        rows = list(rows)
        sizes.append(len(rows))
        return original(rows, **kwargs)

    with patch.object(MessageReadReceipt.objects, "bulk_create", side_effect=create):
        record_reads(conversation, participant, 1201, read_at)
    assert max(sizes) <= 500 and sum(sizes) == 1201
    assert MessageReadReceipt.objects.filter(read_at=read_at).count() == 1201
    record_reads(conversation, participant, 1201, timezone.now())
    assert MessageReadReceipt.objects.count() == 1201
    assert MessageReadReceipt.objects.filter(read_at=read_at).count() == 1201


@pytest.mark.parametrize("size", [1, 30, 100])
def test_rich_event_page_batches_poll_roster_reply_and_actor(size, chat_group):
    from rest_framework.test import APIClient
    from core_apps.chat.models import MessagePoll, ChatEvent
    from core_apps.chat.services.group_cursors import encode_cursor

    _, conversation, owner, peer = chat_group
    original = Message.objects.create(
        conversation=conversation, sender=owner, sequence=1, content="Original"
    )
    messages = Message.objects.bulk_create(
        [
            Message(
                conversation=conversation,
                sender=owner,
                sequence=i + 2,
                kind="poll",
                content="Question",
                reply_to=original,
            )
            for i in range(size)
        ]
    )
    MessagePoll.objects.bulk_create(
        [
            MessagePoll(
                message=message,
                question="Question",
                options=[{"id": "one", "text": "One"}, {"id": "two", "text": "Two"}],
            )
            for message in messages
        ]
    )
    ChatEvent.objects.bulk_create(
        [
            ChatEvent(
                conversation=conversation,
                sequence=i + 1,
                actor=owner,
                message=message,
                kind="message.created",
            )
            for i, message in enumerate(messages)
        ]
    )
    conversation.last_sequence, conversation.last_event_sequence = size + 1, size
    conversation.save(update_fields=["last_sequence", "last_event_sequence"])
    _, participant, _ = authorize(conversation, peer)
    api = APIClient()
    api.force_authenticate(peer)
    cursor = encode_cursor(conversation, participant, "events", 0)

    def get():
        response = api.get(
            f"/api/v1/chat/conversations/{conversation.id}/events/",
            {"after_cursor": cursor, "limit": str(size)},
        )
        assert response.status_code == 200, response.data
        return response.data

    data, report = measured("group-rich-events", size, get)
    assert len(data) == size and report["queries"] <= 25
    assert all(row["payload"]["poll"]["voter_count"] == 0 for row in data)
    assert all(
        row["payload"]["reply_to"]["content_preview"] == "Original" for row in data
    )
