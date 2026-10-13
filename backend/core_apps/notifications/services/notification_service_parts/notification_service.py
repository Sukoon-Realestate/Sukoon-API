"""Notification service: notification service."""

from typing import Any, Dict, Optional
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from core_apps.notifications.models import DeviceToken, Notification
from core_apps.notifications.services.fcm_service import FCMService
from .logger import logger


from .notification_service_operations.notification_inbox import NotificationInboxMixin
from .notification_service_operations.notification_devices import (
    NotificationDevicesMixin,
)
from .notification_service_operations.notification_events import NotificationEventsMixin


class NotificationService(
    NotificationInboxMixin, NotificationDevicesMixin, NotificationEventsMixin
):
    """Public service dispatch with domain-specific responsibilities."""

    """
    Business logic for user notifications and device token management.
    """

    # * High-Level Action Helpers for O-NOTIF-01 & T-NOTIF-01
