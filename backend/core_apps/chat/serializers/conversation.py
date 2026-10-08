from rest_framework import serializers

from core_apps.chat.models import Conversation
from core_apps.chat.serializers.participant import ParticipantSerializer
from core_apps.properties.phone_disclosure import counterpart_phone_payload


class ConversationParticipantSerializer(ParticipantSerializer):
    phone_number = serializers.SerializerMethodField()
    masked_phone_number = serializers.SerializerMethodField()
    is_phone_revealed = serializers.SerializerMethodField()
    phone_notice = serializers.SerializerMethodField()

    def _contact(self, user):
        request = self.context.get("request")
        return counterpart_phone_payload(
            viewer=getattr(request, "user", None),
            counterpart=user,
            request=request,
        )

    def get_phone_number(self, user):
        return self._contact(user)["phone_number"]

    def get_masked_phone_number(self, user):
        return self._contact(user)["masked_phone_number"]

    def get_is_phone_revealed(self, user):
        return self._contact(user)["is_phone_revealed"]

    def get_phone_notice(self, user):
        return self._contact(user)["phone_notice"]


class ConversationSerializer(serializers.ModelSerializer):
    """
    Read representation of a conversation for the conversation list.
    Includes the other participant and the requesting user's unread count.
    """

    other_participant = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    can_send = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            "id",
            "other_participant",
            "last_message_preview",
            "last_message_at",
            "unread_count",
            "can_send",
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
        return ConversationParticipantSerializer(other, context=self.context).data

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

    def get_can_send(self, obj) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_active
            and obj.participants.filter(is_active=True).count() == 2
        )


class ConversationCreateSerializer(serializers.Serializer):
    """
    Start or retrieve a direct conversation.

    Request body:
        {"user_id": "<uuid>"}
    """

    user_id = serializers.UUIDField()
