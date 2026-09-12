from datetime import timedelta
import pytest
from django.utils import timezone

from core_apps.notifications.models import Notification
from core_apps.notifications.serializers import (
    DeviceTokenSerializer,
    DeviceTokenUnregisterSerializer,
    NotificationDetailSerializer,
    NotificationListSerializer,
    format_arabic_time,
    format_arabic_time_ago,
)


@pytest.mark.django_db
class TestNotificationSerializers:
    def test_arabic_time_ago_formatting(self):
        now = timezone.now()
        assert format_arabic_time_ago(now - timedelta(seconds=20)) == "الآن"
        assert format_arabic_time_ago(now - timedelta(minutes=1)) == "منذ دقيقة"
        assert format_arabic_time_ago(now - timedelta(minutes=5)) == "منذ 5 دقائق"
        assert format_arabic_time_ago(now - timedelta(hours=1)) == "منذ ساعة"
        assert format_arabic_time_ago(now - timedelta(hours=3)) == "منذ 3 ساعات"
        assert format_arabic_time_ago(now - timedelta(days=1)) == "منذ يوم"
        assert format_arabic_time_ago(now - timedelta(days=2)) == "منذ يومين"
        assert format_arabic_time_ago(now - timedelta(days=3)) == "منذ 3 أيام"
        assert format_arabic_time_ago(now - timedelta(days=7)) == "منذ أسبوع"
        assert format_arabic_time_ago(None) == ""

    def test_arabic_time_formatting(self):
        dt = timezone.datetime(2026, 1, 14, 14, 55, tzinfo=timezone.utc)
        formatted = format_arabic_time(dt)
        assert "2:55" in formatted
        assert "م" in formatted
        assert format_arabic_time(None) == ""

    def test_notification_list_serializer(self, user):
        notif = Notification.objects.create(
            user=user,
            notification_type=Notification.NotificationType.VISIT_ACCEPTED,
            title="تم قبول طلب زيارتك",
            body="وافق المالك على موعد الزيارة",
            category="حجز زيارة",
            icon_type="check_circle",
        )
        serializer = NotificationListSerializer(notif)
        data = serializer.data
        assert data["title"] == "تم قبول طلب زيارتك"
        assert data["category"] == "حجز زيارة"
        assert data["is_read"] is False
        assert "time_ago" in data

    def test_notification_detail_serializer_with_appointment(self, user):
        notif = Notification.objects.create(
            user=user,
            notification_type=Notification.NotificationType.VISIT_ACCEPTED,
            title="تم قبول طلب زيارتك",
            body="وافق المالك أحمد محمد على موعد الزيارة. يُرجى الحضور في الوقت المحدد للاطلاع على الشقة.",
            category="حجز زيارة",
            icon_type="check_circle",
            data={
                "appointment_date": "الثلاثاء 14 يناير",
                "appointment_time": "3:00 م",
                "address": "مدينة نصر - شارع عباس العقاد",
                "visit_id": "89028448-433c-4113-9118-e36780775d7b",
                "action_label": "عرض الزيارة",
            },
        )
        serializer = NotificationDetailSerializer(notif)
        data = serializer.data
        assert data["title"] == "تم قبول طلب زيارتك"
        assert data["appointment_details"] is not None
        assert data["appointment_details"]["title"] == "تفاصيل الموعد"
        assert "الثلاثاء 14 يناير" in data["appointment_details"]["datetime_label"]
        assert "مدينة نصر - شارع عباس العقاد" == data["appointment_details"]["location_label"]
        assert data["actions"]["primary"]["label"] == "عرض الزيارة"
        assert data["actions"]["secondary"]["label"] == "تجاهل"

    def test_device_token_serializers(self):
        valid_payload = {
            "token": "tok_12345678",
            "device_type": "android",
            "device_name": "Google Pixel",
        }
        ser = DeviceTokenSerializer(data=valid_payload)
        assert ser.is_valid(), ser.errors

        unreg_ser = DeviceTokenUnregisterSerializer(data={"token": "tok_12345678"})
        assert unreg_ser.is_valid(), unreg_ser.errors

        unreg_invalid = DeviceTokenUnregisterSerializer(data={})
        assert not unreg_invalid.is_valid()
