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
        contacts = self.context.setdefault("chat_contacts", {})
        if user.pk not in contacts:
            contacts[user.pk] = counterpart_phone_payload(
                viewer=getattr(request, "user", None),
                counterpart=user,
                request=request,
            )
        return contacts[user.pk]

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
    last_message = serializers.SerializerMethodField()
    policy = serializers.SerializerMethodField()

    def to_representation(self, instance):
        if instance.kind in {"housing_group", "company_request"}:
            from core_apps.chat.services.group_projection import summary

            return summary(instance, self.context["request"].user)
        prepared = self._read(instance)
        value = {"conversation_type": "direct", **super().to_representation(instance)}
        value.update(prepared.preferences)
        latest = prepared.latest
        value["last_message_preview"] = (
            latest.content[:160] if latest and not latest.deleted_at else ""
        )
        value["last_message_at"] = latest.created_at.isoformat() if latest else None
        return value

    class Meta:
        model = Conversation
        fields = (
            "id",
            "other_participant",
            "last_message_preview",
            "last_message",
            "last_message_at",
            "unread_count",
            "can_send",
            "policy",
            "updated_at",
        )
        read_only_fields = fields

    def get_last_message(self, obj):
        from core_apps.chat.services.group_projection import conversation_preview

        request = self.context.get("request")
        if not request or not request.user:
            return None
        latest = self._read(obj).latest
        return conversation_preview(latest, request.user)

    def _read(self, conversation):
        # Local to this serializer/response; never survives another request or
        # authorizes a command, private bytes, transcript or socket dispatch.
        from core_apps.chat.services.read_context import ConversationRead

        if not hasattr(self, "prepared_reads"):
            self.prepared_reads = {}
        if conversation.pk not in self.prepared_reads:
            self.prepared_reads[conversation.pk] = ConversationRead.prepare(
                conversation, self.context["request"].user
            )
        return self.prepared_reads[conversation.pk]

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

    def get_policy(self, obj):
        from core_apps.chat.moderation.policy import projection

        return projection(obj, self.context["request"].user)

    def get_can_send(self, obj) -> bool:
        from core_apps.chat.services.group_access import actions

        return "send_message" in actions(self._read(obj).grant)


class ConversationCreateSerializer(serializers.Serializer):
    """
    Start or retrieve a direct conversation.

    Request body:
        {"user_id": "<uuid>"}
    """

    user_id = serializers.UUIDField()
    workspace = serializers.ChoiceField(
        choices=["individual", "owner", "student"], required=False
    )

    rental_context = serializers.JSONField(required=False)
    expected_visit_revision = serializers.IntegerField(min_value=1, required=False)
