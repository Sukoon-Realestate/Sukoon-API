from rest_framework import serializers

from core_apps.chat.models import Conversation
from core_apps.chat.serializers.participant import ParticipantSerializer


class ConversationSerializer(serializers.ModelSerializer):
    """
    Read representation of a conversation for the conversation list.
    Includes the other participant and the requesting user's unread count.
    """

    other_participant = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            "id",
            "other_participant",
            "last_message_preview",
            "last_message_at",
            "unread_count",
            "updated_at",
        )
        read_only_fields = fields

    def get_other_participant(self, obj):
        request = self.context.get("request")
        if not request or not request.user:
            return None
        request_user = request.user
        # ? Participants are prefetched — filter in Python to avoid extra query
        other = next(
            (p for p in obj.participants.all() if p.pk != request_user.pk),
            None,
        )
        if other is None:
            return None
        return ParticipantSerializer(other, context=self.context).data

    def get_unread_count(self, obj) -> int:
        request = self.context.get("request")
        if not request or not request.user:
            return 0
        request_user = request.user
        # ? participant_set is prefetched with prefetch_related — no extra query
        participant = next(
            (p for p in obj.participant_set.all() if p.user_id == request_user.pk),
            None,
        )
        return participant.unread_count if participant else 0


class ConversationCreateSerializer(serializers.Serializer):
    """
    Start or retrieve a direct conversation.

    Request body:
        {"user_id": "<uuid>"}
    """

    user_id = serializers.UUIDField()
