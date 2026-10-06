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
    property_district = serializers.CharField(
        source="property.district", read_only=True
    )
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


class OwnerPropertyRevenueSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    amount = serializers.FloatField(read_only=True)
    formatted_amount = serializers.CharField(read_only=True)
    currency = serializers.CharField(read_only=True, default="ج")
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(read_only=True)
    status_color = serializers.CharField(read_only=True)
    due_date = serializers.CharField(read_only=True, required=False, allow_null=True)


class OwnerRevenueTransactionSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    date = serializers.CharField(read_only=True)
    date_iso = serializers.CharField(read_only=True)
    amount = serializers.FloatField(read_only=True)
    formatted_amount = serializers.CharField(read_only=True)
    currency = serializers.CharField(read_only=True, default="ج")
    type = serializers.CharField(read_only=True)
    is_credit = serializers.BooleanField(read_only=True)


class OwnerRevenuesSerializer(serializers.Serializer):
    total_this_month = serializers.FloatField(read_only=True)
    formatted_total = serializers.CharField(read_only=True)
    currency = serializers.CharField(read_only=True, default="ج")
    percentage_change = serializers.FloatField(read_only=True)
    comparison_text = serializers.CharField(read_only=True)
    is_positive = serializers.BooleanField(read_only=True)
    properties = OwnerPropertyRevenueSerializer(many=True, read_only=True)
    recent_transactions = OwnerRevenueTransactionSerializer(many=True, read_only=True)


# * =========================================================================
# * Owner Profile Serializers ("ملفي الشخصي")
# * =========================================================================


class OwnerProfileHeaderSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    avatar = serializers.CharField(read_only=True, allow_null=True)
    is_verified = serializers.BooleanField(read_only=True)
    role_badge = serializers.CharField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    reviews_count = serializers.IntegerField(read_only=True)
    rating_label = serializers.CharField(read_only=True)
    member_since_label = serializers.CharField(read_only=True)


class OwnerProfileStatsSerializer(serializers.Serializer):
    properties_count = serializers.IntegerField(read_only=True)
    properties_label = serializers.CharField(read_only=True, default="عقارات")
    reviews_count = serializers.IntegerField(read_only=True)
    reviews_label = serializers.CharField(read_only=True, default="تقييم")
    acceptance_rate = serializers.IntegerField(read_only=True)
    acceptance_label = serializers.CharField(read_only=True, default="قبول")
    formatted_acceptance_rate = serializers.CharField(read_only=True)


class OwnerProfileAccountDetailsSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    masked_phone_number = serializers.CharField(read_only=True)


class OwnerPrivacyNoticeSerializer(serializers.Serializer):
    icon = serializers.CharField(read_only=True, default="lock")
    text = serializers.CharField(read_only=True)


class OwnerRecentReviewSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    reviewer_name = serializers.CharField(read_only=True)
    rating = serializers.IntegerField(read_only=True)
    comment = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class OwnerProfileSerializer(serializers.Serializer):
    """
    Serializer for Owner Profile screen ('ملفي الشخصي').
    """

    owner = OwnerProfileHeaderSerializer(read_only=True)
    stats = OwnerProfileStatsSerializer(read_only=True)
    account_details = OwnerProfileAccountDetailsSerializer(read_only=True)
    privacy_notice = OwnerPrivacyNoticeSerializer(read_only=True)
    recent_reviews = OwnerRecentReviewSerializer(many=True, read_only=True)
