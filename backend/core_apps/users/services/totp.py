"""RFC 6238 factors using the existing cryptography dependency."""

import base64
import hashlib
import secrets
from datetime import timedelta
from cryptography.fernet import Fernet, MultiFernet
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.twofactor.hotp import HOTP
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from ..models import TotpFactor, TotpRecoveryRequest


def cipher():
    return MultiFernet(
        [
            Fernet(
                base64.urlsafe_b64encode(
                    hashlib.sha256(("sokoun-staff-totp-v1:" + key).encode()).digest()
                )
            )
            for key in [
                settings.SECRET_KEY,
                *getattr(settings, "SECRET_KEY_FALLBACKS", []),
            ]
        ]
    )


def seal(secret):
    return cipher().encrypt(secret.encode()).decode()


def unseal(value):
    return cipher().decrypt(value.encode()).decode()


def new_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode()


def code_at(secret, counter, digits=6):
    return HOTP(base64.b32decode(secret), digits, SHA1()).generate(counter).decode()


def pending_recovery(user):
    return TotpRecoveryRequest.objects.filter(user=user, active=True).exists()


def require_sensitive_access(user):
    if user.sensitive_actions_frozen or pending_recovery(user):
        raise PermissionDenied(
            "Sensitive actions are restricted. Existing operation receipts remain available."
        )


def is_staff_account(user):
    from core_apps.admin_api.models import StaffProfile

    return (
        user.is_staff
        or user.is_superuser
        or StaffProfile.objects.filter(user=user).exists()
    )


def check_code(factor, code, *, secret=None):
    """Caller locks the factor and commits failed attempts before raising errors."""
    now = timezone.now()
    if factor.locked_until and factor.locked_until > now:
        return False
    if factor.locked_until:
        factor.failed_attempts = 0
        factor.locked_until = None
    secret = secret or (
        unseal(factor.secret_ciphertext) if factor.secret_ciphertext else ""
    )
    counter = int(now.timestamp()) // 30
    matched = next(
        (
            value
            for value in (counter - 1, counter, counter + 1)
            if secret
            and value > factor.last_counter
            and isinstance(code, str)
            and len(code) == 6
            and code.isascii()
            and code.isdigit()
            and secrets.compare_digest(code_at(secret, value), code)
        ),
        None,
    )
    if matched is None:
        factor.failed_attempts += 1
        if factor.failed_attempts >= 5:
            factor.locked_until = now + timedelta(minutes=5)
    else:
        factor.last_counter = matched
        factor.failed_attempts = 0
        factor.locked_until = None
    factor.save(
        update_fields=["last_counter", "failed_attempts", "locked_until", "updated_at"]
    )
    return matched is not None


def current_factor(user):
    factor = TotpFactor.objects.select_for_update().filter(user=user).first()
    if not factor or not factor.confirmed_at or not factor.secret_ciphertext:
        raise PermissionDenied(
            "Set up your staff verification factor before this action."
        )
    return factor
