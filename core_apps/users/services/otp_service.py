import logging
import secrets
import string
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)

# * OTP Configuration Constants
OTP_LENGTH: int = 6
OTP_EXPIRATION_SECONDS: int = getattr(
    settings, "OTP_EXPIRATION_SECONDS", 600
)  # ? 10 minutes
OTP_COOLDOWN_SECONDS: int = getattr(settings, "OTP_COOLDOWN_SECONDS", 60)  # ? 1 minute
MAX_OTP_ATTEMPTS: int = 5


def generate_otp(length: int = OTP_LENGTH) -> str:
    """
    ? Generate a cryptographically secure numeric OTP string.
    """
    return "".join(secrets.choice(string.digits) for _ in range(length))


def send_otp_email(email: str, otp: str, user_name: str = "") -> bool:
    """
    ? Send the OTP verification code to the given email address.

    ! Catches and logs all email exceptions so SMTP downtime does not crash the request.
    """
    site_name = getattr(settings, "SITE_NAME", "Sukoon") or "Sukoon"
    subject = f"[{site_name}] Verify Your Email - OTP"

    greeting = f"Hello {user_name}," if user_name else "Hello,"
    message = (
        f"{greeting}\n\n"
        f"Your verification code is: {otp}\n\n"
        f"This code will expire in {OTP_EXPIRATION_SECONDS // 60} minutes.\n"
        f"If you did not request this verification, please ignore this email.\n\n"
        f"Best regards,\n"
        f"The {site_name} Team"
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info("OTP verification email sent successfully to %s", email)
        return True
    except Exception as exc:
        # ! Do not crash registration/resend if SMTP fails
        logger.error("Failed to send OTP verification email to %s: %s", email, exc)
        return False


def create_and_send_otp(user: Any) -> str:
    """
    ? Generates a new OTP, stores it in the cache with attempt tracking,
    ? and dispatches the OTP email to the user.
    """
    email = getattr(user, "email", "").strip().lower()
    if not email:
        raise ValidationError({"email": _("User must have a valid email address.")})

    otp = generate_otp()
    cache_key = f"otp:{email}"
    cache_data = {
        "otp": otp,
        "attempts": 0,
        "user_id": str(getattr(user, "id", "")),
    }

    cache.set(cache_key, cache_data, timeout=OTP_EXPIRATION_SECONDS)

    user_name = getattr(user, "get_full_name", "") or getattr(user, "first_name", "")
    send_otp_email(email=email, otp=otp, user_name=user_name)

    return otp


def verify_email_otp(email: str, otp: str) -> Any:
    """
    ? Validates the provided OTP against the cached record.
    ? Marks user.is_verified = True upon success and deletes the cache key.
    """
    if not email:
        raise ValidationError({"email": _("Email is required.")})
    if not otp:
        raise ValidationError({"otp": _("Verification code is required.")})

    normalized_email = email.strip().lower()
    cache_key = f"otp:{normalized_email}"
    record = cache.get(cache_key)

    if not record:
        raise ValidationError(
            {
                "otp": _(
                    "The verification code has expired or is invalid. Please request a new one."
                )
            }
        )

    # * Prevent brute-force attempts
    attempts = record.get("attempts", 0)
    if attempts >= MAX_OTP_ATTEMPTS:
        cache.delete(cache_key)
        raise ValidationError(
            {
                "otp": _(
                    "Too many failed attempts. Please request a new verification code."
                )
            }
        )

    cached_otp = str(record.get("otp", ""))
    submitted_otp = str(otp).strip()

    if not secrets.compare_digest(cached_otp, submitted_otp):
        record["attempts"] = attempts + 1
        cache.set(cache_key, record, timeout=OTP_EXPIRATION_SECONDS)
        raise ValidationError({"otp": _("Invalid verification code.")})

    # * OTP is valid: verify user in the database
    User = get_user_model()
    try:
        user = User.objects.get(email__iexact=normalized_email)
    except User.DoesNotExist:
        raise ValidationError({"email": _("User with this email does not exist.")})

    user.is_verified = True
    user.save(update_fields=["is_verified"])

    # * Invalidate OTP cache and cooldown
    cache.delete(cache_key)
    cache.delete(f"otp_cooldown:{normalized_email}")

    logger.info("User %s (%s) verified email successfully.", user.id, normalized_email)
    return user


def resend_verification_otp(email: str) -> str:
    """
    ? Resends an OTP to the user if eligible (not verified, not in cooldown).
    """
    if not email:
        raise ValidationError({"email": _("Email is required.")})

    normalized_email = email.strip().lower()
    User = get_user_model()

    try:
        user = User.objects.get(email__iexact=normalized_email)
    except User.DoesNotExist:
        raise ValidationError({"email": _("User with this email does not exist.")})

    if user.is_verified:
        raise ValidationError({"email": _("This email is already verified.")})

    # * Cooldown check
    cooldown_key = f"otp_cooldown:{normalized_email}"
    if cache.get(cooldown_key):
        raise ValidationError(
            {"detail": _("Please wait before requesting another verification code.")}
        )

    otp = create_and_send_otp(user)
    cache.set(cooldown_key, True, timeout=OTP_COOLDOWN_SECONDS)

    return otp
