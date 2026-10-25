"""Conversation cards distinguish canonical receipts from unread counters."""

import pytest
from django.utils import timezone
from rest_framework.test import APIRequestFactory
from core_apps.chat.models import Message
from core_apps.chat.serializers.conversation import ConversationSerializer
from core_apps.chat.services.group_projection import summary
from core_apps.chat.services.group_operations import mark_group_read
from core_apps.chat.services.group_send import send_group_message
from .conftest import message_request
from .test_direct_media import direct_chat  # noqa: F401

pytestmark = pytest.mark.django_db


def card(conversation, user):
    request = APIRequestFactory().get("/api/v1/chat/conversations/")
    request.user = user
    return ConversationSerializer(conversation, context={"request": request}).data


def test_direct_card_changes_only_after_counterpart_reads(direct_chat):
    conversation, sender, reader = direct_chat
    message = send_group_message(conversation, sender, message_request("Card receipt"))
    before = card(conversation, sender)["last_message"]
    assert before["sender_id"] == str(sender.pk)
    assert before["read_by_count"] == 0 and before["eligible_reader_count"] == 1
    incoming = card(conversation, reader)
    assert incoming["unread_count"] == 1
    assert incoming["last_message"]["read_by_count"] is None
    mark_group_read(conversation, sender, message.sequence)
    assert card(conversation, sender)["last_message"]["read_by_count"] == 0
    mark_group_read(conversation, reader, message.sequence)
    assert card(conversation, sender)["last_message"]["read_by_count"] == 1
    assert card(conversation, reader)["unread_count"] == 0
    send_group_message(conversation, sender, message_request("New unread"))
    assert card(conversation, sender)["last_message"]["read_by_count"] == 0


def test_legacy_card_uses_existing_read_timestamp_without_upgrading(direct_chat):
    conversation, sender, reader = direct_chat
    message = Message.objects.create(
        conversation=conversation, sender=sender, content="Legacy"
    )
    assert card(conversation, sender)["last_message"]["read_by_count"] == 0
    conversation.participant_set.filter(user=reader).update(last_read_at=timezone.now())
    assert card(conversation, sender)["last_message"]["read_by_count"] == 1
    message.refresh_from_db()
    assert message.sequence is None


def test_legacy_preview_cannot_restore_cleared_history(direct_chat):
    conversation, sender, reader = direct_chat
    Message.objects.create(conversation=conversation, sender=sender, content="Hidden")
    conversation.participant_set.filter(user=reader).update(visible_from_sequence=2)
    hidden = card(conversation, reader)
    assert hidden["last_message"] is None
    assert hidden["last_message_preview"] == ""


def test_group_inbox_matches_history_and_membership_visibility(chat_group):
    group, conversation, sender, reader = chat_group
    message = send_group_message(conversation, sender, message_request("Group receipt"))
    before = summary(conversation, sender)["last_message"]
    assert before["eligible_reader_count"] == 1 and before["read_by_count"] == 0
    mark_group_read(conversation, reader, message.sequence)
    assert summary(conversation, sender)["last_message"]["read_by_count"] == 1
    conversation.participant_set.filter(user=reader).update(
        visible_from_sequence=message.sequence + 1
    )
    assert summary(conversation, sender)["last_message"]["eligible_reader_count"] == 0
    assert summary(conversation, reader)["last_message"] is None
    group.memberships.filter(user=reader).update(status="removed")
    assert summary(conversation, sender)["last_message"]["eligible_reader_count"] == 0


def test_deleted_preview_has_no_content_or_receipt(direct_chat):
    conversation, sender, reader = direct_chat
    message = send_group_message(
        conversation, sender, message_request("Private removed text")
    )
    Message.objects.filter(pk=message.pk).update(deleted_at=timezone.now())
    preview = card(conversation, sender)["last_message"]
    assert preview["is_deleted"] is True
    assert preview["content"] == "" and preview["read_by_count"] is None


def test_empty_conversation_has_no_fabricated_receipt(direct_chat):
    conversation, sender, reader = direct_chat
    assert card(conversation, sender)["last_message"] is None
