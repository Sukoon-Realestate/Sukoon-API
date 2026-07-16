import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from rest_framework.exceptions import ValidationError

GOOGLE_URL = reverse("google-login")
APPLE_URL = reverse("apple-login")
FACEBOOK_URL = reverse("facebook-login")


@pytest.mark.django_db
class TestSocialAuthViews:
    @patch("core_apps.users.views.authenticate_google")
    def test_google_login_success(self, mock_authenticate, api_client, user):
        mock_authenticate.return_value = user
        res = api_client.post(GOOGLE_URL, {"token": "valid-token"}, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert "access" in res.cookies
        assert "refresh" in res.cookies
        assert "logged_in" in res.cookies
        assert res.data["message"] == "Logged in Successfully"
        assert res.data["user"]["email"] == user.email

    @patch("core_apps.users.views.authenticate_google")
    def test_google_login_failure(self, mock_authenticate, api_client):
        mock_authenticate.side_effect = ValidationError(
            "Google token is invalid or expired."
        )
        res = api_client.post(GOOGLE_URL, {"token": "invalid-token"}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    @patch("core_apps.users.views.authenticate_apple")
    def test_apple_login_success(self, mock_authenticate, api_client, user):
        mock_authenticate.return_value = user
        res = api_client.post(
            APPLE_URL,
            {"token": "valid-token", "first_name": "John", "last_name": "Doe"},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        assert "access" in res.cookies
        assert "refresh" in res.cookies
        assert res.data["message"] == "Logged in Successfully"

    @patch("core_apps.users.views.authenticate_facebook")
    def test_facebook_login_success(self, mock_authenticate, api_client, user):
        mock_authenticate.return_value = user
        res = api_client.post(FACEBOOK_URL, {"token": "valid-token"}, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert "access" in res.cookies
        assert "refresh" in res.cookies
        assert res.data["message"] == "Logged in Successfully"
