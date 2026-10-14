"""NotificationDevices operations owned by NotificationService."""

from typing import Any
from django.db import transaction
from rest_framework.exceptions import ValidationError
from core_apps.notifications.models import DeviceToken


class NotificationDevicesMixin:
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

        updated = DeviceToken.objects.filter(user=user, token=token.strip()).update(
            is_active=False
        )
        return bool(updated)
