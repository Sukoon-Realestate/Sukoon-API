import uuid
import pytest
from rest_framework.test import APIRequestFactory

from core_apps.chat.models import Conversation, ConversationParticipant, Message
from core_apps.chat.serializers import (
    ConversationCreateSerializer,
    ConversationSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    ParticipantSerializer,
)


@pytest.mark.django_db
class TestChatSerializers:
    def test_participant_serializer(self, user):
        serializer = ParticipantSerializer(user)
        data = serializer.data
        assert data["id"] == str(user.id)
        assert data["email"] == user.email
        assert data["full_name"] == user.get_full_name
        assert "avatar_url" in data
        assert "is_online" in data

    def test_conversation_serializer(self, user, another_user):
        conversation = Conversation.objects.create(
            last_message_preview="Hello there",
        )
        ConversationParticipant.objects.create(
            conversation=conversation, user=user, unread_count=3
        )
        ConversationParticipant.objects.create(
            conversation=conversation, user=another_user, unread_count=0
        )

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = user

        serializer = ConversationSerializer(conversation, context={"request": request})
        data = serializer.data

        assert data["id"] == str(conversation.id)
        assert data["last_message_preview"] == "Hello there"
        assert data["unread_count"] == 3
        assert data["other_participant"]["id"] == str(another_user.id)

    def test_conversation_create_serializer_valid(self):
        uid = str(uuid.uuid4())
        serializer = ConversationCreateSerializer(data={"user_id": uid})
        assert serializer.is_valid()
        assert str(serializer.validated_data["user_id"]) == uid

    def test_conversation_create_serializer_invalid(self):
        serializer = ConversationCreateSerializer(data={"user_id": "not-a-uuid"})
        assert not serializer.is_valid()
        assert "user_id" in serializer.errors

    def test_message_serializer(self, user, another_user):
        conversation = Conversation.objects.create()
        ConversationParticipant.objects.create(conversation=conversation, user=user)
        ConversationParticipant.objects.create(
            conversation=conversation, user=another_user
        )

        message = Message.objects.create(
            conversation=conversation, sender=user, content="Is the flat furnished?"
        )

        serializer = MessageSerializer(message)
        data = serializer.data

        assert data["id"] == str(message.id)
        assert data["content"] == "Is the flat furnished?"
        assert data["sender"]["id"] == str(user.id)
        assert data["conversation"] == conversation.pkid

    def test_message_create_serializer(self):
        serializer = MessageCreateSerializer(data={"content": "Valid message"})
        assert serializer.is_valid()
        assert serializer.validated_data["content"] == "Valid message"

        empty = MessageCreateSerializer(data={"content": ""})
        assert not empty.is_valid()
        assert "content" in empty.errors
