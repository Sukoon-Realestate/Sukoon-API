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
        auth_session=None,
        language="ar",
    ) -> DeviceToken:
        """
        Registers or updates an FCM device token for the user.
        """
        if not token or not token.strip():
            raise ValidationError({"token": "Device token is required."})

        if auth_session is not None:
            from core_apps.users.models import AuthSession, User
            from django.utils import timezone

            # Serialize registration with account/session revocation.
            current = User.objects.select_for_update().get(pk=user.pk)
            auth_session = (
                AuthSession.objects.select_for_update()
                .filter(
                    id=auth_session,
                    user=current,
                    revoked_at__isnull=True,
                    security_epoch=current.security_epoch,
                    expires_at__gt=timezone.now(),
                )
                .first()
            )
            if auth_session is None:
                raise ValidationError("Sign in again before registering notifications.")
        device, _ = DeviceToken.objects.update_or_create(
            token=token.strip(),
            defaults={
                "user": user,
                "auth_session": auth_session,
                "device_type": device_type,
                "device_name": device_name.strip(),
                "language": language if language in {"ar", "en"} else "ar",
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
