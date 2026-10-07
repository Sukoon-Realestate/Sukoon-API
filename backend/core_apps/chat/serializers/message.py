from rest_framework import serializers

from core_apps.chat.models import Message
from core_apps.chat.serializers.participant import ParticipantSerializer


class MessageSerializer(serializers.ModelSerializer):
    sender = ParticipantSerializer(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "sender",
            "content",
            "client_message_id",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "conversation", "created_at")

    def get_status(self, obj):
        return "sent"


class MessageCreateSerializer(serializers.Serializer):
    """
    Send a message in a conversation.

    Request body:
        {"content": "Hello, is this property still available?"}
    """

    content = serializers.CharField(max_length=5000)
    client_message_id = serializers.UUIDField(required=False)
