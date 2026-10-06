import logging
from typing import Any
from django.dispatch import receiver
from djoser.signals import user_registered

from core_apps.users.services.otp_service import create_and_send_otp

logger = logging.getLogger(__name__)


@receiver(user_registered)
def on_user_registered(
    sender: Any, user: Any, request: Any = None, **kwargs: Any
) -> None:
    """
    ? Automatically generates and dispatches an OTP verification email
    ? when a user registers via Djoser's endpoint.
    """
    try:
        create_and_send_otp(user)
        logger.info(
            "Dispatched OTP verification for registered user %s",
            getattr(user, "email", ""),
        )
    except Exception as exc:
        logger.error(
            "Failed to dispatch OTP verification for user %s: %s",
            getattr(user, "email", ""),
            exc,
        )
