import logging
from typing import Any, Dict, Optional
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from core_apps.notifications.models import DeviceToken, Notification
from core_apps.notifications.services.fcm_service import FCMService

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Business logic for user notifications and device token management.
    """

    @classmethod
    def create_notification(
        cls,
        user: Any,
        title: str,
        body: str = "",
        notification_type: str = Notification.NotificationType.GENERAL,
        category: str = "",
        icon_type: str = "bell",
        data: Optional[Dict[str, Any]] = None,
        send_push: bool = True,
    ) -> Notification:
        """
        Creates an in-app notification and optionally dispatches an FCM push.
        """
        if not title:
            raise ValidationError({"title": "Notification title is required."})

        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            body=body,
            category=category,
            icon_type=icon_type,
            data=data or {},
        )

        if send_push:
            try:
                FCMService.send_push_to_user(
                    user=user,
                    title=title,
                    body=body,
                    data=data,
                    notification_type=notification_type,
                )
            except Exception as exc:
                logger.error("Failed to trigger FCM push for notification %s: %s", notification.id, exc)

        return notification

    @classmethod
    def get_user_notifications(
        cls, user: Any, unread_only: bool = False
    ) -> QuerySet[Notification]:
        """
        Returns notifications belonging to the user.
        """
        queryset = Notification.objects.filter(user=user)
        if unread_only:
            queryset = queryset.filter(is_read=False)
        return queryset.order_by("-created_at")

    @classmethod
    def get_notification_detail(cls, user: Any, notification_id: str) -> Notification:
        """
        Retrieves a single notification and marks it as read.
        """
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
        except Notification.DoesNotExist:
            raise NotFound("Notification not found.")

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at", "updated_at"])

        return notification

    @classmethod
    def mark_as_read(cls, user: Any, notification_id: str) -> Notification:
        """
        Marks a specific notification as read.
        """
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
        except Notification.DoesNotExist:
            raise NotFound("Notification not found.")

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at", "updated_at"])

        return notification

    @classmethod
    def mark_all_as_read(cls, user: Any) -> int:
        """
        Marks all unread notifications for the user as read ("تحديد الكل كمقروء").
        """
        now = timezone.now()
        count = Notification.objects.filter(user=user, is_read=False).update(
            is_read=True, read_at=now, updated_at=now
        )
        return count

    @classmethod
    def get_unread_count(cls, user: Any) -> int:
        """
        Returns the count of unread notifications for the user.
        """
        return Notification.objects.filter(user=user, is_read=False).count()

    @classmethod
    @transaction.atomic
    def register_device_token(
        cls,
        user: Any,
        token: str,
        device_type: str = DeviceToken.DeviceType.ANDROID,
        device_name: str = "",
    ) -> DeviceToken:
        """
        Registers or updates an FCM device token for the user.
        """
        if not token or not token.strip():
            raise ValidationError({"token": "Device token is required."})

        device, _ = DeviceToken.objects.update_or_create(
            token=token.strip(),
            defaults={
                "user": user,
                "device_type": device_type,
                "device_name": device_name.strip(),
                "is_active": True,
            },
        )
        return device

    @classmethod
    def unregister_device_token(cls, user: Any, token: str) -> bool:
        """
        Deactivates an FCM device token.
        """
        if not token or not token.strip():
            raise ValidationError({"token": "Device token is required."})

        updated = DeviceToken.objects.filter(
            user=user, token=token.strip()
        ).update(is_active=False)
        return bool(updated)

    # * High-Level Action Helpers for O-NOTIF-01 & T-NOTIF-01

    @classmethod
    def notify_property_verified(cls, property_obj: Any) -> Notification:
        """
        Screen: O-NOTIF-01 Item 4 ('عقارك تم توثيقه').
        Fired when a property is approved and verified.
        """
        return cls.create_notification(
            user=property_obj.owner,
            notification_type=Notification.NotificationType.PROPERTY_VERIFIED,
            title="عقارك تم توثيقه",
            body=f"{property_obj.title} - يظهر الآن في نتائج البحث",
            category="توثيق العقار",
            icon_type="verified",
            data={
                "property_id": str(property_obj.id),
                "action_label": "عرض العقار",
                "action_type": "view_property",
            },
        )

    @classmethod
    def notify_property_views_milestone(
        cls, property_obj: Any, views_count: int = 50
    ) -> Notification:
        """
        Screen: O-NOTIF-01 Item 3 ('شقتك حصلت على 50 مشاهدة').
        Fired when a property crosses an impression/views milestone.
        """
        return cls.create_notification(
            user=property_obj.owner,
            notification_type=Notification.NotificationType.PROPERTY_VIEWS,
            title=f"شقتك حصلت على {views_count} مشاهدة",
            body=f"{property_obj.title} - أداء متميز هذا الأسبوع",
            category="أداء العقار",
            icon_type="eye",
            data={
                "property_id": str(property_obj.id),
                "views_count": views_count,
                "action_label": "عرض الإحصائيات",
                "action_type": "view_property_stats",
            },
        )

    @classmethod
    def notify_daily_bump_reminder(cls, owner: Any) -> Notification:
        """
        Screen: O-NOTIF-01 Item 5 ('تحديث الظهور اليومي').
        Fired as a daily reminder for property owners.
        """
        return cls.create_notification(
            user=owner,
            notification_type=Notification.NotificationType.DAILY_BUMP,
            title="تحديث الظهور اليومي",
            body="حدّث عقاراتك يومياً للحفاظ على ترتيبها في البحث",
            category="تحديث العقارات",
            icon_type="warning",
            data={
                "action_label": "تحديث الآن",
                "action_type": "bump_properties",
            },
        )

    @classmethod
    def notify_new_message(
        cls,
        sender: Any,
        receiver: Any,
        message_preview: str,
        chat_id: Optional[str] = None,
        is_from_owner: bool = False,
    ) -> Notification:
        """
        Screens: T-NOTIF-01 Item 5 & O-NOTIF-01 Item 2 ('رسالة جديدة').
        Fired when a new chat message arrives.
        """
        title = "رسالة جديدة من المالك" if is_from_owner else "رسالة جديدة من مستأجر"
        sender_name = sender.get_full_name or sender.email.split("@")[0]
        preview = message_preview[:80]
        body = f"{sender_name}: {preview}"

        return cls.create_notification(
            user=receiver,
            notification_type=Notification.NotificationType.NEW_MESSAGE,
            title=title,
            body=body,
            category="الرسائل",
            icon_type="chat",
            data={
                "chat_id": str(chat_id) if chat_id else "",
                "sender_id": str(sender.id),
                "sender_name": sender_name,
                "action_label": "فتح المحادثة",
                "action_type": "open_chat",
            },
        )
