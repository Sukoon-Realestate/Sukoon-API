"""Visit: tenant visit list serializer."""

from rest_framework import serializers
from core_apps.profiles.serializers import CloudinarySerializerField
from ...phone_disclosure import counterpart_phone_payload
from ...models import PropertyVisit
from .property_visit_serializer import (
    _ARABIC_WEEKDAYS,
    _ENGLISH_WEEKDAYS,
    _ARABIC_MONTHS,
    _ENGLISH_MONTHS,
    _ARABIC_VISIT_STATUS,
    _ENGLISH_VISIT_STATUS,
    get_visit_language,
    User,
    PostVisitContextMixin,
)


class TenantVisitListSerializer(serializers.ModelSerializer):
    """
    Card-style serializer for a tenant's own visit requests.

    Returns a compact Arabic-formatted payload matching the visit card UI:
    property title + district, visit day, time and status label.
    """

    title = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = PropertyVisit
        fields = ["id", "title", "status", "note", "created_at"]
        read_only_fields = fields

    def get_title(self, obj: PropertyVisit) -> str:
        return f"{obj.property.title} - {obj.property.district}"

    def _lang(self) -> str:
        return get_visit_language(self.context)



    def get_status(self, obj: PropertyVisit) -> str:
        lang = self._lang()
        table = _ENGLISH_VISIT_STATUS if lang == "en" else _ARABIC_VISIT_STATUS
        return table.get(obj.status, obj.status)


class VisitTenantSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="get_full_name", read_only=True)
    # ? DRF returns None here if the tenant has no profile/avatar
    avatar = CloudinarySerializerField(source="profile.avatar", read_only=True)
    phone_number = serializers.SerializerMethodField()
    masked_phone_number = serializers.SerializerMethodField()
    is_phone_revealed = serializers.SerializerMethodField()
    phone_notice = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "avatar",
            "is_verified",
            "phone_number",
            "masked_phone_number",
            "is_phone_revealed",
            "phone_notice",
        ]
        read_only_fields = fields

    def _contact(self, obj):
        return counterpart_phone_payload(
            viewer=getattr(self.context.get("request"), "user", None),
            counterpart=obj,
            request=self.context.get("request"),
            visit=self.context.get("visit"),
        )

    def get_phone_number(self, obj):
        return self._contact(obj)["phone_number"]

    def get_masked_phone_number(self, obj):
        return self._contact(obj)["masked_phone_number"]

    def get_is_phone_revealed(self, obj):
        return self._contact(obj)["is_phone_revealed"]

    def get_phone_notice(self, obj):
        return self._contact(obj)["phone_notice"]


class PropertyVisitDetailSerializer(PostVisitContextMixin, serializers.ModelSerializer):
    tenant = serializers.SerializerMethodField()
    property_id = serializers.UUIDField(source="property.id", read_only=True)

    class Meta:
        model = PropertyVisit
        fields = [
            "id",
            "property_id",
            "tenant",
            "status",
        ]
        read_only_fields = fields


    def get_tenant(self, obj):
        return VisitTenantSerializer(
            obj.tenant,
            context={"request": self.context.get("request"), "visit": obj},
        ).data
