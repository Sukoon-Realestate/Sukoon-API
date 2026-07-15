import pytest
from django.urls import reverse
from rest_framework import status

LOGIN_URL = reverse("login")
REFRESH_URL = reverse("refresh")
LOGOUT_URL = "/api/v1/auth/logout/"


@pytest.mark.django_db
class TestLoginView:
    def test_login_success_sets_auth_cookies(self, api_client, user):
        res = api_client.post(
            LOGIN_URL,
            {"email": "user@example.com", "password": "Testpass123!"},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        assert "access" in res.cookies
        assert "refresh" in res.cookies
        assert "logged_in" in res.cookies

    def test_login_removes_tokens_from_response_body(self, api_client, user):
        res = api_client.post(
            LOGIN_URL,
            {"email": "user@example.com", "password": "Testpass123!"},
            format="json",
        )
        assert "access" not in res.data
        assert "refresh" not in res.data
        assert res.data["message"] == "Logged in Successfully"

    def test_login_wrong_password_returns_401(self, api_client, user):
        res = api_client.post(
            LOGIN_URL,
            {"email": "user@example.com", "password": "wrongpass"},
            format="json",
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_email_returns_401(self, api_client, db):
        res = api_client.post(
            LOGIN_URL,
            {"email": "ghost@example.com", "password": "pass123"},
            format="json",
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLogoutView:
    def test_logout_clears_auth_cookies(self, auth_client):
        """Bug: Response(status.HTTP_204_NO_CONTENT) sets data=204, not status."""
        res = auth_client.post(LOGOUT_URL)
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert res.cookies["access"].value == ""
        assert res.cookies["refresh"].value == ""
        assert res.cookies["logged_in"].value == ""


@pytest.mark.django_db
class TestTokenRefreshView:
    def test_refresh_without_cookie_returns_400(self, api_client):
        """Bug was: refresh_res unbound when no cookie → UnboundLocalError (500)."""
        res = api_client.post(REFRESH_URL)
        assert res.status_code == status.HTTP_400_BAD_REQUEST
