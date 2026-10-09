from rest_framework import serializers

from core_apps.support.models import Ticket, TicketAttachment, TicketMessage


class TicketAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = TicketAttachment
        fields = ["id", "name", "url"]
        read_only_fields = fields

    def get_url(self, obj) -> str:
        request = self.context.get("request")
        if obj.file and hasattr(obj.file, "url"):
            url = obj.file.url
            if request and not url.startswith("http"):
                return request.build_absolute_uri(url)
            return url
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

    class Meta:
        model = Ticket
        fields = [
            "id",
            "reference",
            "subject",
            "category",
            "status",
            "created_at",
            "messages",
            "rental_context",
        ]
        read_only_fields = fields


class TicketCreateSerializer(serializers.Serializer):
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
    body = serializers.CharField(
        min_length=1,
        max_length=4000,
        trim_whitespace=True,
    )
