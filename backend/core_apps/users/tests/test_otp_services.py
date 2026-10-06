import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from rest_framework.exceptions import ValidationError

from core_apps.users.services.otp_service import (
    generate_otp,
    send_otp_email,
    create_and_send_otp,
    verify_email_otp,
    resend_verification_otp,
    OTP_LENGTH,
    MAX_OTP_ATTEMPTS,
)
from core_apps.users.services.user_service import register_user

User = get_user_model()


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestOtpService:
    def test_generate_otp_format(self):
        otp = generate_otp()
        assert len(otp) == OTP_LENGTH
        assert otp.isdigit()

    def test_generate_otp_custom_length(self):
        otp = generate_otp(length=8)
        assert len(otp) == 8
        assert otp.isdigit()

    def test_send_otp_email_success(self):
        result = send_otp_email("test@example.com", "123456", user_name="John")
        assert result is True
        assert len(mail.outbox) == 1
        assert "123456" in mail.outbox[0].body
        assert "test@example.com" in mail.outbox[0].to

    def test_send_otp_email_resilient_to_exception(self):
        with patch(
            "core_apps.users.services.otp_service.send_mail",
            side_effect=OSError("SMTP timeout"),
        ):
            result = send_otp_email("test@example.com", "123456")
            assert result is False

    def test_create_and_send_otp_stores_in_cache(self, user):
        otp = create_and_send_otp(user)
        assert len(otp) == 6
        assert len(mail.outbox) == 1
        assert otp in mail.outbox[0].body

        cached = cache.get(f"otp:{user.email.lower()}")
        assert cached is not None
        assert cached["otp"] == otp
        assert cached["attempts"] == 0
        assert cached["user_id"] == str(user.id)

    def test_verify_email_otp_success(self, user):
        user.is_verified = False
        user.save(update_fields=["is_verified"])

        otp = create_and_send_otp(user)
        verified_user = verify_email_otp(user.email, otp)

        assert verified_user.id == user.id
        assert verified_user.is_verified is True

        user.refresh_from_db()
        assert user.is_verified is True
        assert cache.get(f"otp:{user.email.lower()}") is None

    def test_verify_email_otp_invalid_code_raises(self, user):
        create_and_send_otp(user)

        with pytest.raises(ValidationError) as exc_info:
            verify_email_otp(user.email, "000000")

        assert "Invalid verification code" in str(exc_info.value)
        cached = cache.get(f"otp:{user.email.lower()}")
        assert cached["attempts"] == 1

    def test_verify_email_otp_expired_or_missing_raises(self, user):
        with pytest.raises(ValidationError) as exc_info:
            verify_email_otp(user.email, "123456")

        assert "expired or is invalid" in str(exc_info.value)

    def test_verify_email_otp_brute_force_lockout(self, user):
        create_and_send_otp(user)

        # Fail MAX_OTP_ATTEMPTS times
        for _ in range(MAX_OTP_ATTEMPTS):
            try:
                verify_email_otp(user.email, "999999")
            except ValidationError:
                pass

        # Next attempt should inform user of too many failed attempts and purge cache
        with pytest.raises(ValidationError) as exc_info:
            verify_email_otp(user.email, "999999")

        assert "Too many failed attempts" in str(exc_info.value)
        assert cache.get(f"otp:{user.email.lower()}") is None

    def test_resend_verification_otp_success(self, user):
        user.is_verified = False
        user.save(update_fields=["is_verified"])

        otp = resend_verification_otp(user.email)
        assert len(otp) == 6
        assert len(mail.outbox) == 1
        assert cache.get(f"otp:{user.email.lower()}")["otp"] == otp
        assert cache.get(f"otp_cooldown:{user.email.lower()}") is True

    def test_resend_verification_otp_cooldown_raises(self, user):
        user.is_verified = False
        user.save(update_fields=["is_verified"])

        resend_verification_otp(user.email)

        with pytest.raises(ValidationError) as exc_info:
            resend_verification_otp(user.email)

        assert "Please wait before requesting another" in str(exc_info.value)

    def test_resend_verification_otp_already_verified_raises(self, user):
        user.is_verified = True
        user.save(update_fields=["is_verified"])

        with pytest.raises(ValidationError) as exc_info:
            resend_verification_otp(user.email)

        assert "already verified" in str(exc_info.value)

    def test_register_user_service_creates_user_and_dispatches_otp(self):
        data = {
            "first_name": "Service",
            "last_name": "Test",
            "email": "servicetest@example.com",
            "password": "Password123!",
            "re_password": "Password123!",
            "birth_date": "1990-01-01",
            "phone_number": "+201000000000",
        }

        user = register_user(data)
        assert user.email == "servicetest@example.com"
        assert user.is_verified is False
        assert user.profile.birth_date is not None
        assert str(user.profile.phone_number) == "+201000000000"

        # OTP is in cache and outbox
        cached = cache.get("otp:servicetest@example.com")
        assert cached is not None
        assert len(mail.outbox) == 1
        assert cached["otp"] in mail.outbox[0].body
