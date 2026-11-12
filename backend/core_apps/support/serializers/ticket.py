from rest_framework import serializers

from core_apps.support.models import Ticket, TicketAttachment, TicketMessage


class PreparedRelationSerializer(serializers.ListSerializer):
    """Keep nested serializer contracts while using an authorized prepared page."""

    def get_attribute(self, instance):
        name = f"prepared_{self.field_name}"
        if hasattr(instance, name):
            return getattr(instance, name)
        return super().get_attribute(instance)


class TicketAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = TicketAttachment
        list_serializer_class = PreparedRelationSerializer
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
    def to_representation(self, instance):
        value = super().to_representation(instance)
        if hasattr(instance, "read_pages"):
            value["pages"] = instance.read_pages
        return value

    attachments = TicketAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = TicketMessage
        list_serializer_class = PreparedRelationSerializer
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
    information_requests = serializers.SerializerMethodField()

    def get_information_requests(self, obj):
        from core_apps.support.services.information import projection
        return projection(obj)

    messages = TicketMessageSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        value = super().to_representation(instance)
        pages = getattr(instance, "read_bounds", None)
        if pages:
            value["pages"] = pages.metadata
        return value

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
            "information_requests",
            "rental_context",
        ]
        read_only_fields = fields


class TicketCreateSerializer(serializers.Serializer):
    attachment_ids = serializers.ListField(
        child=serializers.UUIDField(), max_length=3, required=False
    )
    rental_context = serializers.JSONField(required=False, default=dict)
    workspace = serializers.ChoiceField(
        choices=Ticket.Workspace.values,
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
    information_request_id = serializers.UUIDField(required=False)
    information_revision = serializers.IntegerField(min_value=1, required=False)

    attachment_ids = serializers.ListField(
        child=serializers.UUIDField(), max_length=3, required=False
    )
    body = serializers.CharField(
        allow_blank=True,
        max_length=4000,
        trim_whitespace=True,
    )

    def validate(self, attrs):
        if ("information_request_id" in attrs) != ("information_revision" in attrs):
            raise serializers.ValidationError("Supply the information request and its current revision together.")
        if not attrs["body"] and not attrs.get("attachment_ids"):
            raise serializers.ValidationError(
                {"body": "Supply a reply or an attachment."}
            )
        return attrs
