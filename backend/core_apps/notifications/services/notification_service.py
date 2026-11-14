"""Stable public imports for notification service.

Implementation modules separate domain responsibilities without changing routes.
"""

import logging
from typing import Any, Dict, Optional
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from core_apps.notifications.models import DeviceToken, Notification
from core_apps.notifications.services.fcm_service import FCMService

from .notification_service_parts.logger import (
    logger,
)
from .notification_service_parts.notification_service import (
    NotificationService,
)

# Preserve the existing public import surface, including compatibility seams.
__all__ = [
    'logging',
    'Any',
    'Dict',
    'Optional',
    'transaction',
    'QuerySet',
    'timezone',
    'NotFound',
    'ValidationError',
    'DeviceToken',
    'Notification',
    'FCMService',
    'logger',
    'NotificationService',
]
