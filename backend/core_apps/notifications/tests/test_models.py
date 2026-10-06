import pytest
from core_apps.notifications.models import DeviceToken, Notification


@pytest.mark.django_db
class TestNotificationModel:
    def test_notification_creation_and_str(self, user):
        notif = Notification.objects.create(
            user=user,
            notification_type=Notification.NotificationType.VISIT_ACCEPTED,
            title="تم قبول طلب زيارتك",
            body="وافق المالك على موعد الزيارة",
            category="حجز زيارة",
            icon_type="check_circle",
            data={"visit_id": "123"},
        )
        assert notif.pkid is not None
        assert notif.id is not None
        assert notif.is_read is False
        assert notif.read_at is None
        assert notif.title == "تم قبول طلب زيارتك"
        assert str(notif) == f"تم قبول طلب زيارتك -> {user.email}"

    def test_device_token_creation_and_str(self, user):
        device = DeviceToken.objects.create(
            user=user,
            token="fcm_token_sample_1234567890abcdef",
            device_type=DeviceToken.DeviceType.ANDROID,
            device_name="Samsung S23",
        )
        assert device.pkid is not None
        assert device.is_active is True
        assert "Samsung S23" in device.device_name
        assert "android" in str(device)
