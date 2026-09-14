from rest_framework import serializers

from core_apps.chat.models import Message
from core_apps.chat.serializers.participant import ParticipantSerializer


class MessageSerializer(serializers.ModelSerializer):
    sender = ParticipantSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "conversation", "sender", "content", "created_at")
        read_only_fields = ("id", "conversation", "created_at")


class MessageCreateSerializer(serializers.Serializer):
    """
    Send a message in a conversation.

    Request body:
        {"content": "Hello, is this property still available?"}
    """

    content = serializers.CharField(max_length=5000)
