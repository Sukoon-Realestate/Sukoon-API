from django.contrib.auth import get_user_model
from rest_framework import serializers

from core_apps.profiles.serializers import CloudinarySerializerField

from ..models import PropertyVisit

User = get_user_model()


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


def _format_time_ar(value):
    hour = value.hour
    minute = value.minute
    period = "ص" if hour < 12 else "م"
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12
    if minute == 0:
        return f"{hour_12}{period}"
    return f"{hour_12}:{minute:02d}{period}"


def _format_date_label(value):
    from django.utils import timezone

    today = timezone.localdate()
    if value == today:
        return "النهاره"
    if value == today + timezone.timedelta(days=1):
        return "غداً"
    weekday = _ARABIC_WEEKDAYS[value.weekday()]
    month = _ARABIC_MONTHS[value.month]
    return f"{weekday} {value.day} {month}"


class OwnerDashboardOwnerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="get_full_name", read_only=True)
    avatar = CloudinarySerializerField(source="profile.avatar", read_only=True)

    class Meta:
        model = User
        fields = ["name", "avatar", "is_verified"]
        read_only_fields = fields


class OwnerDashboardPendingVisitSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.get_full_name", read_only=True)
    tenant_avatar = CloudinarySerializerField(
        source="tenant.profile.avatar", read_only=True
    )
    property_title = serializers.CharField(source="property.title", read_only=True)
    property_district = serializers.CharField(source="property.district", read_only=True)
    scheduled_at = serializers.SerializerMethodField()

    class Meta:
        model = PropertyVisit
        fields = [
            "id",
            "tenant_name",
            "tenant_avatar",
            "property_title",
            "property_district",
            "scheduled_at",
        ]
        read_only_fields = fields

    def get_scheduled_at(self, obj: PropertyVisit) -> str:
        date_label = _format_date_label(obj.visit_date)
        time_label = _format_time_ar(obj.visit_time)
        return f"{date_label} {time_label}"


class OwnerDashboardSerializer(serializers.Serializer):
    owner = OwnerDashboardOwnerSerializer(read_only=True)
    visits_this_week = serializers.IntegerField(read_only=True)
    active_properties = serializers.IntegerField(read_only=True)
    overall_rating = serializers.FloatField(read_only=True)
    pending_requests = serializers.IntegerField(read_only=True)
    pending_visits = OwnerDashboardPendingVisitSerializer(many=True, read_only=True)
