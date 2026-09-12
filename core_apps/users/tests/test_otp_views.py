import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

from core_apps.users.services.otp_service import create_and_send_otp

User = get_user_model()

REGISTER_URL = reverse("user-register")
VERIFY_URL = reverse("verify-email")
RESEND_URL = reverse("resend-otp")
DJOSER_REGISTER_URL = "/api/v1/auth/users/"


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestRegisterView:
    def test_register_success_creates_user_and_sends_otp(self, api_client):
        payload = {
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@example.com",
            "password": "ValidPassword123!",
            "re_password": "ValidPassword123!",
        }

        res = api_client.post(REGISTER_URL, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert "A verification code has been sent to your email" in res.data.get(
            "message", ""
        )

        created_user = User.objects.get(email="newuser@example.com")
        assert created_user.is_verified is False
        assert created_user.first_name == "New"

        # Check email was sent with OTP
        assert len(mail.outbox) == 1
        assert "newuser@example.com" in mail.outbox[0].to

        # Check OTP is in cache
        cached = cache.get("otp:newuser@example.com")
        assert cached is not None
        assert cached["otp"] in mail.outbox[0].body

    def test_register_duplicate_email_returns_400(self, api_client, user):
        payload = {
            "first_name": "Another",
            "last_name": "User",
            "email": user.email,
            "password": "ValidPassword123!",
            "re_password": "ValidPassword123!",
        }

        res = api_client.post(REGISTER_URL, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch_returns_400(self, api_client):
        payload = {
            "first_name": "Mismatch",
            "last_name": "User",
            "email": "mismatch@example.com",
            "password": "Password123!",
            "re_password": "DifferentPassword123!",
        }

        res = api_client.post(REGISTER_URL, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_via_djoser_endpoint_triggers_otp(self, api_client):
        payload = {
            "first_name": "Djoser",
            "last_name": "Reg",
            "email": "djoseruser@example.com",
            "password": "Password123!",
            "re_password": "Password123!",
        }

        res = api_client.post(DJOSER_REGISTER_URL, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED

        # Djoser user_registered signal should trigger create_and_send_otp
        assert len(mail.outbox) == 1
        assert "djoseruser@example.com" in mail.outbox[0].to
        cached = cache.get("otp:djoseruser@example.com")
        assert cached is not None
        assert cached["otp"] in mail.outbox[0].body


@pytest.mark.django_db
class TestVerifyEmailView:
    def test_verify_email_success(self, api_client, user):
        user.is_verified = False
        user.save(update_fields=["is_verified"])

        otp = create_and_send_otp(user)

        res = api_client.post(
            VERIFY_URL,
            {"email": user.email, "otp": otp},
            format="json",
        )

        assert res.status_code == status.HTTP_200_OK
        assert "Email verified successfully" in res.data.get("message", "")

        user.refresh_from_db()
        assert user.is_verified is True

        # Auth cookies set
        assert "access" in res.cookies
        assert "refresh" in res.cookies
        assert "logged_in" in res.cookies
        assert res.cookies["logged_in"].value == "true"

    def test_verify_email_alias_endpoint(self, api_client, user):
        user.is_verified = False
        user.save(update_fields=["is_verified"])

        otp = create_and_send_otp(user)

        res = api_client.post(
            "/api/v1/auth/verify-email/",
            {"email": user.email, "otp": otp},
            format="json",
        )

        assert res.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_verified is True

    def test_verify_email_wrong_otp_returns_400(self, api_client, user):
        create_and_send_otp(user)

        res = api_client.post(
            VERIFY_URL,
            {"email": user.email, "otp": "999999"},
            format="json",
        )

        assert res.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.is_verified is False

    def test_verify_email_expired_otp_returns_400(self, api_client, user):
        res = api_client.post(
            VERIFY_URL,
            {"email": user.email, "otp": "123456"},
            format="json",
        )

        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_email_invalid_otp_format_returns_400(self, api_client, user):
        res = api_client.post(
            VERIFY_URL,
            {"email": user.email, "otp": "abc"},
            format="json",
        )

        assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestResendOtpView:
    def test_resend_otp_success(self, api_client, user):
        user.is_verified = False
        user.save(update_fields=["is_verified"])

        res = api_client.post(
            RESEND_URL,
            {"email": user.email},
            format="json",
        )

        assert res.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1
        assert "A new verification code has been sent" in res.data.get("message", "")

    def test_resend_otp_cooldown_returns_400(self, api_client, user):
        user.is_verified = False
        user.save(update_fields=["is_verified"])

        res1 = api_client.post(RESEND_URL, {"email": user.email}, format="json")
        assert res1.status_code == status.HTTP_200_OK

        res2 = api_client.post(RESEND_URL, {"email": user.email}, format="json")
        assert res2.status_code == status.HTTP_400_BAD_REQUEST

    def test_resend_otp_already_verified_returns_400(self, api_client, user):
        user.is_verified = True
        user.save(update_fields=["is_verified"])

        res = api_client.post(RESEND_URL, {"email": user.email}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_resend_otp_nonexistent_email_returns_400(self, api_client):
        res = api_client.post(RESEND_URL, {"email": "ghost@example.com"}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
