import pytest
import uuid
from rest_framework.exceptions import ValidationError

from core_apps.chat.models import Conversation, ConversationParticipant, Message
from core_apps.chat.services.message_service import (
    ChatMessageConflict,
    get_or_create_direct_conversation,
    is_user_online,
    mark_conversation_read,
    send_message,
    set_user_online_status,
)


@pytest.mark.django_db
class TestChatServices:
    def test_get_or_create_direct_conversation_happy_path(self, user, another_user):
        conv = get_or_create_direct_conversation(user=user, other_user=another_user)
        assert conv is not None
        assert conv.participants.count() == 2
        assert conv.participants.filter(pk=user.pk).exists()
        assert conv.participants.filter(pk=another_user.pk).exists()

    def test_get_or_create_direct_conversation_idempotent(self, user, another_user):
        conv1 = get_or_create_direct_conversation(user=user, other_user=another_user)
        conv2 = get_or_create_direct_conversation(user=user, other_user=another_user)
        conv3 = get_or_create_direct_conversation(user=another_user, other_user=user)

        assert conv1.pkid == conv2.pkid == conv3.pkid
        assert Conversation.objects.count() == 1

    def test_get_or_create_direct_conversation_self_chat_raises_error(self, user):
        with pytest.raises(ValidationError) as exc:
            get_or_create_direct_conversation(user=user, other_user=user)
        assert "user_id" in exc.value.detail

    def test_send_message_updates_preview_and_increments_unread(
        self, user, another_user
    ):
        conv = get_or_create_direct_conversation(user=user, other_user=another_user)

        msg = send_message(
            conversation=conv,
            sender=user,
            content="Hello from Egypt!",
        )

        assert msg.content == "Hello from Egypt!"
        assert msg.sender == user
        assert msg.conversation == conv

        conv.refresh_from_db()
        assert conv.last_message_preview == "Hello from Egypt!"
        assert conv.last_message_at == msg.created_at

        # Check unread count
        user_part = ConversationParticipant.objects.get(conversation=conv, user=user)
        other_part = ConversationParticipant.objects.get(
            conversation=conv, user=another_user
        )

        assert user_part.unread_count == 0  # sender unread_count untouched
        assert other_part.unread_count == 1  # recipient unread_count incremented

        # Send second message
        send_message(
            conversation=conv,
            sender=user,
            content="Are you available tomorrow?",
        )
        other_part.refresh_from_db()
        assert other_part.unread_count == 2

    def test_send_message_non_participant_raises_error(
        self, user, another_user, superuser
    ):
        conv = get_or_create_direct_conversation(user=user, other_user=another_user)

        with pytest.raises(ValidationError) as exc:
            send_message(
                conversation=conv,
                sender=superuser,
                content="I'm intruding!",
            )
        assert "content" in exc.value.detail

    def test_client_message_id_replays_one_message_and_conflicts_on_changed_text(
        self, user, another_user
    ):
        conv = get_or_create_direct_conversation(user=user, other_user=another_user)
        client_message_id = uuid.uuid4()

        first = send_message(
            conversation=conv,
            sender=user,
            content="Retry-safe text",
            client_message_id=client_message_id,
        )
        replay = send_message(
            conversation=conv,
            sender=user,
            content="Retry-safe text",
            client_message_id=client_message_id,
        )

        assert replay.id == first.id
        assert Message.objects.filter(conversation=conv).count() == 1
        with pytest.raises(ChatMessageConflict):
            send_message(
                conversation=conv,
                sender=user,
                content="Changed text",
                client_message_id=client_message_id,
            )

    def test_mark_conversation_read_resets_unread_count(self, user, another_user):
        conv = get_or_create_direct_conversation(user=user, other_user=another_user)
        send_message(conversation=conv, sender=user, content="Message 1")
        send_message(conversation=conv, sender=user, content="Message 2")

        recipient_part = ConversationParticipant.objects.get(
            conversation=conv, user=another_user
        )
        assert recipient_part.unread_count == 2

        mark_conversation_read(conversation=conv, user=another_user)

        recipient_part.refresh_from_db()
        assert recipient_part.unread_count == 0
        assert recipient_part.last_read_at is not None

    def test_user_online_status(self, user):
        uid = str(user.id)
        assert is_user_online(uid) is False

        set_user_online_status(uid, True)
        assert is_user_online(uid) is True

        set_user_online_status(uid, False)
        assert is_user_online(uid) is False
