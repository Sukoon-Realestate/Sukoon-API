"""NotificationInbox operations owned by NotificationService."""

from typing import Any, Dict, Optional
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from core_apps.notifications.models import Notification
from core_apps.notifications.services.fcm_service import FCMService
from ..logger import logger
from core_apps.notifications.services.inbox_scope import filter_scope


class NotificationInboxMixin:
    @classmethod
    @transaction.atomic
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
            from core_apps.notifications.services.push_delivery import (
                queue_notification,
            )

            queue_notification(notification)

        return notification

    @classmethod
    def get_user_notifications(
        cls, user: Any, unread_only: bool = False, *, scope=None
    ) -> QuerySet[Notification]:
        """
        Returns notifications belonging to the user.
        """
        queryset = filter_scope(Notification.objects.filter(user=user), scope)
        if unread_only:
            queryset = queryset.filter(is_read=False)
        return queryset.order_by("-created_at", "-pkid")

    @classmethod
    def get_notification_detail(cls, user: Any, notification_id: str) -> Notification:
        """
        Retrieves a single notification and marks it as read.
        """
        try:
            notification = filter_scope(
                Notification.objects.filter(user=user), None
            ).get(id=notification_id)
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
            notification = filter_scope(
                Notification.objects.filter(user=user), None
            ).get(id=notification_id)
        except Notification.DoesNotExist:
            raise NotFound("Notification not found.")

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at", "updated_at"])

        return notification

    @classmethod
    def mark_all_as_read(cls, user: Any, *, scope=None) -> int:
        """
        Marks all unread notifications for the user as read ("تحديد الكل كمقروء").
        """
        now = timezone.now()
        count = filter_scope(
            Notification.objects.filter(user=user, is_read=False), scope
        ).update(is_read=True, read_at=now, updated_at=now)
        return count

    @classmethod
    def get_unread_count(cls, user: Any, *, scope=None) -> int:
        """
        Returns the count of unread notifications for the user.
        """
        return filter_scope(
            Notification.objects.filter(user=user, is_read=False), scope
        ).count()
