import uuid
from unittest.mock import patch
import pytest
from rest_framework.exceptions import NotFound, ValidationError

from core_apps.notifications.models import DeviceToken, Notification
from core_apps.notifications.services import NotificationService


@pytest.mark.django_db
class TestNotificationService:
    @patch("core_apps.notifications.services.fcm_service.FCMService.send_push_to_user")
    def test_create_notification_triggers_push(self, mock_send_push, user):
        notif = NotificationService.create_notification(
            user=user,
            title="طلب جديد",
            body="تفاصيل الطلب",
            notification_type=Notification.NotificationType.VISIT_REQUEST,
            send_push=True,
        )
        assert notif.id is not None
        assert notif.title == "طلب جديد"
        mock_send_push.assert_called_once()

    def test_create_notification_missing_title_raises_validation_error(self, user):
        with pytest.raises(ValidationError):
            NotificationService.create_notification(user=user, title="")

    def test_get_user_notifications_and_unread_filtering(self, user, another_user):
        n1 = Notification.objects.create(user=user, title="N1", is_read=False)
        n2 = Notification.objects.create(user=user, title="N2", is_read=True)
        Notification.objects.create(user=another_user, title="N3", is_read=False)

        all_user_notifs = NotificationService.get_user_notifications(user)
        assert all_user_notifs.count() == 2

        unread_notifs = NotificationService.get_user_notifications(user, unread_only=True)
        assert unread_notifs.count() == 1
        assert unread_notifs.first().id == n1.id

    def test_get_notification_detail_marks_read(self, user):
        notif = Notification.objects.create(user=user, title="Unread", is_read=False)
        assert notif.is_read is False

        fetched = NotificationService.get_notification_detail(user, str(notif.id))
        assert fetched.is_read is True
        assert fetched.read_at is not None

    def test_get_notification_detail_not_found(self, user, another_user):
        notif = Notification.objects.create(user=another_user, title="Other", is_read=False)
        with pytest.raises(NotFound):
            NotificationService.get_notification_detail(user, str(notif.id))

    def test_mark_as_read(self, user):
        notif = Notification.objects.create(user=user, title="Unread", is_read=False)
        updated = NotificationService.mark_as_read(user, str(notif.id))
        assert updated.is_read is True
        assert updated.read_at is not None

    def test_mark_all_as_read(self, user, another_user):
        Notification.objects.create(user=user, title="N1", is_read=False)
        Notification.objects.create(user=user, title="N2", is_read=False)
        Notification.objects.create(user=user, title="N3", is_read=True)
        Notification.objects.create(user=another_user, title="Other", is_read=False)

        count = NotificationService.mark_all_as_read(user)
        assert count == 2

        # Verify all user's notifications are now read
        assert NotificationService.get_unread_count(user) == 0
        # Another user's unread notification remains untouched
        assert NotificationService.get_unread_count(another_user) == 1

    def test_register_and_unregister_device_token(self, user):
        device = NotificationService.register_device_token(
            user=user,
            token="device_token_xyz_123",
            device_type="ios",
            device_name="iPhone 15",
        )
        assert device.is_active is True
        assert device.device_type == "ios"

        # Re-registering updates existing token
        device2 = NotificationService.register_device_token(
            user=user,
            token="device_token_xyz_123",
            device_type="ios",
            device_name="iPhone 15 Pro",
        )
        assert device2.id == device.id
        assert device2.device_name == "iPhone 15 Pro"

        # Unregister
        result = NotificationService.unregister_device_token(user, "device_token_xyz_123")
        assert result is True
        device.refresh_from_db()
        assert device.is_active is False

    @patch("core_apps.notifications.services.fcm_service.FCMService.send_push_to_user")
    def test_action_helpers(self, mock_send_push, user, another_user):
        class MockProperty:
            id = uuid.uuid4()
            title = "شقة مدينة نصر"
            owner = user

        mock_prop = MockProperty()

        # 1. Property verified
        n_verified = NotificationService.notify_property_verified(mock_prop)
        assert n_verified.title == "عقارك تم توثيقه"
        assert n_verified.user == user

        # 2. Views milestone
        n_views = NotificationService.notify_property_views_milestone(mock_prop, 50)
        assert "50" in n_views.title
        assert n_views.user == user

        # 3. Daily bump reminder
        n_bump = NotificationService.notify_daily_bump_reminder(user)
        assert n_bump.title == "تحديث الظهور اليومي"
        assert n_bump.user == user

        # 4. New message
        n_msg = NotificationService.notify_new_message(
            sender=another_user,
            receiver=user,
            message_preview="هل الشقة لسه متاحة؟",
            is_from_owner=False,
        )
        assert n_msg.title == "رسالة جديدة من مستأجر"
        assert "هل الشقة لسه متاحة؟" in n_msg.body
