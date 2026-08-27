from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core_apps.profiles.serializers import CloudinarySerializerField
from core_apps.properties.serializers.property import PropertyListSerializer
from ..models import PropertyVisit
from ..services import PropertyVisitService


# ? Arabic date/time labels for the tenant visit card UI
_ARABIC_WEEKDAYS = {
    0: "الإثنين",
    1: "الثلاثاء",
    2: "الأربعاء",
    3: "الخميس",
    4: "الجمعة",
    5: "السبت",
    6: "الأحد",
}

_ARABIC_MONTHS = {
    1: "يناير",
    2: "فبراير",
    3: "مارس",
    4: "أبريل",
    5: "مايو",
    6: "يونيو",
    7: "يوليو",
    8: "أغسطس",
    9: "سبتمبر",
    10: "أكتوبر",
    11: "نوفمبر",
    12: "ديسمبر",
}

_ARABIC_VISIT_STATUS = {
    PropertyVisit.Status.PENDING: "بانتظار رد المالك",
    PropertyVisit.Status.CONFIRMED: "مؤكد",
    PropertyVisit.Status.CANCELED: "ملغي",
    PropertyVisit.Status.REJECTED: "مرفوض",
}

User = get_user_model()


class PropertyVisitSerializer(serializers.ModelSerializer):
    property = PropertyListSerializer(read_only=True)
    tenant_name = serializers.CharField(source="tenant.get_full_name", read_only=True)
    tenant_email = serializers.SerializerMethodField()

    class Meta:
        model = PropertyVisit
        fields = [
            "id",
            "property",
            "tenant_name",
            "tenant_email",
            "visit_date",
            "visit_time",
            "status",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def get_tenant_email(self, obj):
        request = self.context.get("request")
        if request and request.user:
            # Tenant can always see their own email
            if request.user == obj.tenant:
                return obj.tenant.email
            # Owner can only see the tenant's email if the visit is confirmed
            if (
                request.user == obj.property.owner
                and obj.status == PropertyVisit.Status.CONFIRMED
            ):
                return obj.tenant.email
        return ""


class TenantVisitListSerializer(serializers.ModelSerializer):
    """
    Card-style serializer for a tenant's own visit requests.

    Returns a compact Arabic-formatted payload matching the visit card UI:
    property title + district, visit day, time and status label.
    """

    title = serializers.SerializerMethodField()
    day = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = PropertyVisit
        fields = ["id", "title", "day", "time", "status"]
        read_only_fields = fields

    def get_title(self, obj: PropertyVisit) -> str:
        return f"{obj.property.title} - {obj.property.district}"

    def get_day(self, obj: PropertyVisit) -> str:
        weekday = _ARABIC_WEEKDAYS[obj.visit_date.weekday()]
        month = _ARABIC_MONTHS[obj.visit_date.month]
        return f"{weekday} {obj.visit_date.day} {month}"

    def get_time(self, obj: PropertyVisit) -> str:
        hour = obj.visit_time.hour
        minute = obj.visit_time.minute
        period = "ص" if hour < 12 else "م"
        hour_12 = hour % 12
        if hour_12 == 0:
            hour_12 = 12
        return f"{hour_12}:{minute:02d} {period}"

    def get_status(self, obj: PropertyVisit) -> str:
        return _ARABIC_VISIT_STATUS.get(obj.status, obj.status)


class VisitTenantSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="get_full_name", read_only=True)
    # ? DRF returns None here if the tenant has no profile/avatar
    avatar = CloudinarySerializerField(source="profile.avatar", read_only=True)

    class Meta:
        model = User
        fields = ["name", "avatar", "is_verified"]
        read_only_fields = fields


class PropertyVisitDetailSerializer(serializers.ModelSerializer):
    tenant = VisitTenantSerializer(read_only=True)

    class Meta:
        model = PropertyVisit
        fields = ["id", "tenant", "visit_date", "status"]
        read_only_fields = fields


class PropertyVisitCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyVisit
        fields = ["id", "visit_date", "visit_time", "note", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_visit_date(self, value):
        from django.utils import timezone

        if value < timezone.localdate():
            raise serializers.ValidationError(_("Visit date cannot be in the past."))
        return value

    def create(self, validated_data):
        tenant = validated_data.pop("tenant")
        property_obj = validated_data.pop("property_obj")
        return PropertyVisitService.create_visit(
            tenant=tenant, property_obj=property_obj, validated_data=validated_data
        )


class PropertyVisitUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyVisit
        fields = ["status"]

    def update(self, instance, validated_data):
        user = self.context["request"].user
        status = validated_data.get("status")
        return PropertyVisitService.update_visit_status(
            user=user, visit_obj=instance, status=status
        )


class AvailableDatesQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
