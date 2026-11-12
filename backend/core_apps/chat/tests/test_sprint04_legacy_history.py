"""Legacy direct-message pages batch presence without rich relation payloads."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from core_apps.chat.models import (
    ChatPresenceLease, ConversationParticipant, Message, MessagePoll,
    MessagePollVote, MessageStar,
)
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from tools.qa.performance import measured

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("size", [1, 10, 100])
def test_legacy_history_presence_and_unused_relations(size, user, another_user, auth_client):
    conversation = get_or_create_direct_conversation(user=user, other_user=another_user)
    ConversationParticipant.objects.filter(conversation=conversation).update(membership_period=uuid4())
    messages = Message.objects.bulk_create([
        Message(conversation=conversation, sender=another_user, sequence=i + 1,
                content=f"Synthetic {i}", system_data={"unused": "x" * 10000})
        for i in range(size)
    ])
    polls = MessagePoll.objects.bulk_create([
        MessagePoll(message=row, question="Unused", options=[{"id": "one"}]) for row in messages
    ])
    MessagePollVote.objects.bulk_create([
        MessagePollVote(poll=poll, user=user, membership_period=uuid4(), option_ids=["one"])
        for poll in polls
    ])
    MessageStar.objects.bulk_create([
        MessageStar(message=row, user=user, membership_period=uuid4()) for row in messages
    ])
    ChatPresenceLease.objects.create(
        connection_id=f"synthetic-{another_user.id}", user=another_user,
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    url = reverse("message-list", kwargs={"id": conversation.id})

    def get():
        response = auth_client.get(url, {"page_size": size})
        assert response.status_code == 200
        response.render()
        return response

    with CaptureQueriesContext(connection) as captured:
        response, report = measured("legacy-direct-message-history", size, get)
    rows = response.data["results"]
    assert len(rows) == size
    assert [row["id"] for row in rows] == [str(row.id) for row in messages]
    assert all(row["sender"]["is_online"] and row["sender"]["email"] == "" for row in rows)
    assert set(rows[0]) == {"id", "conversation", "sender", "content", "client_message_id",
                            "status", "is_forwarded", "created_at"}
    from types import SimpleNamespace
    from core_apps.chat.serializers.message import MessageSerializer

    # No prepared context: compare every value with the original nested
    # serializer/fallback, using the same saved rows rather than random fixtures.
    original = MessageSerializer(
        Message.objects.filter(pk__in=[row.pk for row in messages])
        .select_related("sender", "sender__profile").order_by("created_at"),
        many=True, context={"request": SimpleNamespace(user=user)},
    ).data
    assert rows == original
    assert report["queries"] <= 16
    assert sum('chat_chatpresencelease' in item["sql"].lower() for item in captured) == 1
    assert not any(
        'chat_messagestar' in item["sql"].lower() or 'chat_messagepoll' in item["sql"].lower()
        for item in captured
    )
    assert not any('"system_data"' in item["sql"] for item in captured)
    ChatPresenceLease.objects.filter(user=another_user).update(expires_at=timezone.now() - timedelta(seconds=1))
    assert not get().data["results"][0]["sender"]["is_online"]


def test_presence_is_page_scoped_and_does_not_run_before_authorization(user, another_user, superuser, auth_client):
    conversation = get_or_create_direct_conversation(user=user, other_user=another_user)
    ConversationParticipant.objects.filter(conversation=conversation).update(membership_period=uuid4())
    Message.objects.bulk_create([
        Message(conversation=conversation, sender=user if i == 0 else another_user,
                sequence=i + 1, content="Synthetic") for i in range(2)
    ])
    ChatPresenceLease.objects.create(
        connection_id="synthetic-online", user=another_user,
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    url = reverse("message-list", kwargs={"id": conversation.id})
    first = auth_client.get(url, {"page_size": 1})
    second = auth_client.get(url, {"page_size": 1, "page": 2})
    assert first.status_code == second.status_code == 200
    assert not first.data["results"][0]["sender"]["is_online"]
    assert first.data["results"][0]["sender"]["email"] == user.email
    assert second.data["results"][0]["sender"]["is_online"]
    auth_client.force_authenticate(superuser)
    with CaptureQueriesContext(connection) as captured:
        response = auth_client.get(url)
    assert response.status_code == 403
    assert not any('chat_chatpresencelease' in item["sql"].lower() for item in captured)


def test_presence_unavailable_retains_offline_fallback(user, another_user, auth_client):
    from unittest.mock import patch

    conversation = get_or_create_direct_conversation(user=user, other_user=another_user)
    ConversationParticipant.objects.filter(conversation=conversation).update(membership_period=uuid4())
    Message.objects.create(conversation=conversation, sender=another_user, sequence=1, content="Synthetic")
    with patch.object(ChatPresenceLease.objects, "filter", side_effect=RuntimeError("Synthetic outage")):
        response = auth_client.get(reverse("message-list", kwargs={"id": conversation.id}))
    assert response.status_code == 200
    assert not response.data["results"][0]["sender"]["is_online"]
