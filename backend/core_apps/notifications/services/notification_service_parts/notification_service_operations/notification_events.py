"""NotificationEvents operations owned by NotificationService."""

from typing import Any, Optional
from core_apps.notifications.models import Notification


class NotificationEventsMixin:
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
