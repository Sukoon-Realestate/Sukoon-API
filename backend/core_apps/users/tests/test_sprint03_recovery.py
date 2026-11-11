"""Sprint 03 identity adapters and serialized OTP recovery."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import connection, close_old_connections
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken
from djoser.conf import settings as djoser_settings

from core_apps.users.services import otp_service
from core_apps.users.services.sessions import revoke_all, validate_session
from core_apps.users.views_parts.set_auth_cookies import CustomTokenRefreshView


@pytest.mark.django_db
@pytest.mark.parametrize("format", ["json", "multipart"])
@pytest.mark.parametrize("cookie", [False, True])
def test_refresh_supported_bodies_and_cookie_precedence(user, format, cookie):
    issued = djoser_settings.SOCIAL_AUTH_TOKEN_STRATEGY.obtain(user)
    factory = APIRequestFactory()
    request = factory.post(
        "/auth/jwt/refresh/", {"refresh": "bad" if cookie else issued["refresh"]}, format=format
    )
    if cookie:
        request.COOKIES["refresh"] = issued["refresh"]
    result = CustomTokenRefreshView.as_view()(request)
    assert result.status_code == 200, result.data
    assert result.data == {"message": "Token Refreshed Successfully"}
    assert "access" in result.cookies and "refresh" in result.cookies


@pytest.mark.django_db
def test_refresh_urlencoded_and_malformed_body(user):
    token = djoser_settings.SOCIAL_AUTH_TOKEN_STRATEGY.obtain(user)["refresh"]
    factory = APIRequestFactory()
    request = factory.post(
        "/", f"refresh={token}", content_type="application/x-www-form-urlencoded"
    )
    assert CustomTokenRefreshView.as_view()(request).status_code == 200
    for body in ([], "invalid", {"refresh": []}, {"refresh": "garbage"}, {}):
        request = factory.post("/", body, format="json")
        assert CustomTokenRefreshView.as_view()(request).status_code in {400, 401}


@pytest.mark.django_db
def test_legacy_social_issuer_after_recovery_is_bound_and_revocable(user):
    current = revoke_all(user)
    tokens = djoser_settings.SOCIAL_AUTH_TOKEN_STRATEGY.obtain(current)
    refresh = RefreshToken(tokens["refresh"])
    assert refresh["session_id"] and refresh["security_epoch"] == current.security_epoch
    validate_session(current, refresh.access_token)
    current = revoke_all(current)
    with pytest.raises(Exception) as error:
        validate_session(current, refresh.access_token)
    assert "revoked" in str(error.value).lower()


def concurrent_calls(count, operation):
    barrier = Barrier(count)

    def run(index):
        close_old_connections()
        try:
            barrier.wait(timeout=15)
            try:
                operation(index)
                return "ok"
            except ValidationError:
                return "rejected"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=count) as pool:
        return list(pool.map(run, range(count)))


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("operation", ["consume", "attempts", "resend"])
def test_postgres_otp_serializes_consume_attempts_and_resend(user, monkeypatch, operation):
    if connection.vendor != "postgresql":
        pytest.skip("Requires disposable PostgreSQL row locks")
    monkeypatch.setattr(otp_service, "send_otp_email", lambda **kwargs: True)
    monkeypatch.setattr(otp_service, "generate_otp", lambda: "123456")
    code = otp_service.create_and_send_otp(user)
    if operation == "consume":
        results = concurrent_calls(4, lambda _: otp_service.verify_email_otp(user.email, code))
        assert results.count("ok") == 1
    elif operation == "attempts":
        results = concurrent_calls(8, lambda _: otp_service.verify_email_otp(user.email, "654321"))
        assert results == ["rejected"] * 8
        assert cache.get(f"otp:{user.email}") is None
        with pytest.raises(ValidationError):
            otp_service.verify_email_otp(user.email, code)
    else:
        results = concurrent_calls(4, lambda _: otp_service.resend_verification_otp(user.email))
        assert results.count("ok") == 1
