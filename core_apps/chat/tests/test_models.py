import pytest
from django.db import IntegrityError

from core_apps.chat.models import Conversation, ConversationParticipant, Message


@pytest.mark.django_db
class TestChatModels:
    def test_create_conversation_and_str(self):
        conversation = Conversation.objects.create(
            last_message_preview="Hello world",
        )
        assert conversation.id is not None
        assert conversation.pkid is not None
        assert str(conversation) == f"Conversation {conversation.id}"
        assert conversation.last_message_preview == "Hello world"

    def test_conversation_participant_and_unique_constraint(self, user, another_user):
        conversation = Conversation.objects.create()
        participant1 = ConversationParticipant.objects.create(
            conversation=conversation, user=user, unread_count=2
        )
        participant2 = ConversationParticipant.objects.create(
            conversation=conversation, user=another_user
        )

        assert str(participant1) == f"{user.email} in {conversation.id}"
        assert participant1.unread_count == 2
        assert participant2.unread_count == 0

        # Unique constraint: cannot add the same user twice to the same conversation
        with pytest.raises(IntegrityError):
            ConversationParticipant.objects.create(conversation=conversation, user=user)

    def test_message_creation_and_ordering(self, user, another_user):
        conversation = Conversation.objects.create()
        ConversationParticipant.objects.create(conversation=conversation, user=user)
        ConversationParticipant.objects.create(
            conversation=conversation, user=another_user
        )

        msg1 = Message.objects.create(
            conversation=conversation, sender=user, content="First message"
        )
        msg2 = Message.objects.create(
            conversation=conversation, sender=another_user, content="Second message"
        )

        messages = list(conversation.messages.all())
        assert len(messages) == 2
        assert messages[0] == msg1
        assert messages[1] == msg2
        assert (
            str(msg1) == f"{user.email} @ {msg1.created_at:%H:%M} in {conversation.id}"
        )
