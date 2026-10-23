from rest_framework import serializers

from core_apps.support.models import Ticket, TicketAttachment, TicketMessage


class TicketAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = TicketAttachment
        fields = ["id", "name", "url", "status", "media_metadata"]
        read_only_fields = fields

    def get_url(self, obj) -> str:
        request = self.context.get("request")
        url = obj.file_url
        if url:
            url += f"?workspace={obj.message.ticket.workspace}"
            return request.build_absolute_uri(url) if request else url
        return ""


class TicketMessageSerializer(serializers.ModelSerializer):
    attachments = TicketAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = TicketMessage
        fields = ["id", "sender", "body", "created_at", "attachments"]
        read_only_fields = fields


class TicketListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            "id",
            "reference",
            "subject",
            "category",
            "status",
            "created_at",
            "updated_at",
            "rental_context",
        ]
        read_only_fields = fields


class TicketDetailSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)
    rental_context = serializers.SerializerMethodField()

    def get_rental_context(self, obj):
        context = dict(obj.rental_context)
        request = self.context.get("request")
        # General support remains available before verification. The financial
        # case workspace has its own verified-account prerequisite.
        if request is not None and not request.user.is_verified:
            context.pop("case_id", None)
        return context

    class Meta:
        model = Ticket
        fields = [
            "id",
            "reference",
            "revision",
            "subject",
            "category",
            "status",
            "created_at",
            "messages",
            "rental_context",
        ]
        read_only_fields = fields


class TicketCreateSerializer(serializers.Serializer):
    attachment_ids = serializers.ListField(
        child=serializers.UUIDField(), max_length=3, required=False
    )
    rental_context = serializers.JSONField(required=False, default=dict)
    workspace = serializers.ChoiceField(
        choices=["tenant", "owner"],
        default="tenant",
    )
    category = serializers.ChoiceField(
        choices=[
            "visit",
            "payment",
            "verification",
            "property",
            "report_owner",
            "report_tenant",
            "other",
        ],
    )
    subject = serializers.CharField(
        min_length=3,
        max_length=160,
        trim_whitespace=True,
    )
    description = serializers.CharField(
        min_length=10,
        max_length=4000,
        trim_whitespace=True,
    )


class TicketReplySerializer(serializers.Serializer):
    attachment_ids = serializers.ListField(
        child=serializers.UUIDField(), max_length=3, required=False
    )
    body = serializers.CharField(
        allow_blank=True,
        max_length=4000,
        trim_whitespace=True,
    )

    def validate(self, attrs):
        if not attrs["body"] and not attrs.get("attachment_ids"):
            raise serializers.ValidationError(
                {"body": "Supply a reply or an attachment."}
            )
        return attrs
