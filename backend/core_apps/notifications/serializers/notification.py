from typing import Any, Dict, Optional
from django.utils import timezone
from rest_framework import serializers

from core_apps.notifications.models import Notification


def format_arabic_time_ago(dt) -> str:
    """
    Returns Arabic relative time string matching T-NOTIF-01 UI design.
    Examples: 'الآن', 'منذ 5 دقائق', 'منذ ساعة', 'منذ يومين', 'منذ 3 أيام', 'منذ أسبوع'
    """
    if not dt:
        return ""
    now = timezone.now()
    diff = now - dt
    total_seconds = max(0, int(diff.total_seconds()))

    if total_seconds < 60:
        return "الآن"

    minutes = total_seconds // 60
    if minutes < 60:
        if minutes == 1:
            return "منذ دقيقة"
        if minutes == 2:
            return "منذ دقيقتين"
        if 3 <= minutes <= 10:
            return f"منذ {minutes} دقائق"
        return f"منذ {minutes} دقيقة"

    hours = total_seconds // 3600
    if hours < 24:
        if hours == 1:
            return "منذ ساعة"
        if hours == 2:
            return "منذ ساعتين"
        if 3 <= hours <= 10:
            return f"منذ {hours} ساعات"
        return f"منذ {hours} ساعة"

    days = total_seconds // 86400
    if days < 7:
        if days == 1:
            return "منذ يوم"
        if days == 2:
            return "منذ يومين"
        if 3 <= days <= 10:
            return f"منذ {days} أيام"
        return f"منذ {days} يوم"

    weeks = days // 7
    if weeks == 1:
        return "منذ أسبوع"
    if weeks == 2:
        return "منذ أسبوعين"
    if 3 <= weeks <= 10:
        return f"منذ {weeks} أسابيع"
    return f"منذ {weeks} أسبوع"


def format_arabic_time(dt) -> str:
    """
    Returns Arabic 12-hour formatted time (e.g., '2:55 م' or '10:00 ص').
    """
    if not dt:
        return ""
    hour = dt.strftime("%I").lstrip("0") or "12"
    minute = dt.strftime("%M")
    period = "ص" if dt.strftime("%p") == "AM" else "م"
    return f"{hour}:{minute} {period}"


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Serializer for T-NOTIF-01 (Notification List Screen).
    """

    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "body",
            "category",
            "icon_type",
            "is_read",
            "created_at",
            "time_ago",
            "data",
        ]
        read_only_fields = fields

    def get_time_ago(self, obj: Notification) -> str:
        return format_arabic_time_ago(obj.created_at)


class NotificationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for T-NOTIF-02 (Notification Details Screen).
    """

    time_ago = serializers.SerializerMethodField()
    formatted_time = serializers.SerializerMethodField()
    appointment_details = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "body",
            "category",
            "icon_type",
            "is_read",
            "read_at",
            "created_at",
            "time_ago",
            "formatted_time",
            "appointment_details",
            "actions",
            "data",
        ]
        read_only_fields = fields

    def get_time_ago(self, obj: Notification) -> str:
        return format_arabic_time_ago(obj.created_at)

    def get_formatted_time(self, obj: Notification) -> str:
        return format_arabic_time(obj.created_at)

    def get_appointment_details(self, obj: Notification) -> Optional[Dict[str, Any]]:
        """
        Extracts structured appointment box details if present in payload (T-NOTIF-02 card).
        """
        data = obj.data or {}
        date_val = data.get("appointment_date") or data.get("visit_date")
        time_val = data.get("appointment_time") or data.get("visit_time")
        address_val = data.get("address") or data.get("location")

        if date_val or time_val or address_val:
            time_str = f"{date_val} ، {time_val}" if date_val and time_val else (date_val or time_val or "")
            return {
                "title": "تفاصيل الموعد",
                "datetime_label": time_str,
                "location_label": address_val or "",
            }
        return None

    def get_actions(self, obj: Notification) -> Dict[str, Any]:
        """
        Provides primary and secondary action definitions for T-NOTIF-02.
        """
        data = obj.data or {}
        action_type = data.get("action_type") or "view_visit"
        target_id = data.get("target_id") or data.get("visit_id") or data.get("property_id")
        primary_label = data.get("action_label")

        if not primary_label:
            if (
                "visit" in obj.notification_type
                or "زيارة" in obj.category
                or "زيار" in obj.title
            ):
                primary_label = "عرض الزيارة"
            elif (
                "property" in obj.notification_type
                or "عقار" in obj.category
                or "عقار" in obj.title
            ):
                primary_label = "عرض العقار"
            elif (
                "message" in obj.notification_type
                or "رسال" in obj.category
                or "رسال" in obj.title
            ):
                primary_label = "فتح المحادثة"
            else:
                primary_label = "عرض التفاصيل"

        return {
            "primary": {
                "label": primary_label,
                "action_type": action_type,
                "target_id": str(target_id) if target_id else None,
            },
            "secondary": {
                "label": "تجاهل",
                "action_type": "dismiss",
            },
        }
