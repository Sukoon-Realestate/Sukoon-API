import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()
SET_PASSWORD_URL = "/api/v1/auth/users/set_password/"


@pytest.mark.django_db
class TestSetPasswordAPIView:
    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.post(SET_PASSWORD_URL, {})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_wrong_current_password_returns_400(self, auth_client, user):
        payload = {
            "current_password": "WrongPassword123!",
            "new_password": "ValidNewPass123!",
            "re_new_password": "ValidNewPass123!",
        }
        res = auth_client.post(SET_PASSWORD_URL, payload)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_mismatched_new_passwords_returns_400(self, auth_client, user):
        payload = {
            "current_password": "Password123!",
            "new_password": "ValidNewPass123!",
            "re_new_password": "DifferentPass123!",
        }
        res = auth_client.post(SET_PASSWORD_URL, payload)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_short_new_password_returns_400(self, auth_client, user):
        payload = {
            "current_password": "Password123!",
            "new_password": "short",
            "re_new_password": "short",
        }
        res = auth_client.post(SET_PASSWORD_URL, payload)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_social_user_without_usable_password_returns_400(self, auth_client, user):
        user.set_unusable_password()
        user.save()

        payload = {
            "current_password": "AnyPassword123!",
            "new_password": "ValidNewPass123!",
            "re_new_password": "ValidNewPass123!",
        }
        res = auth_client.post(SET_PASSWORD_URL, payload)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_set_password_happy_path(self, auth_client, user):
        payload = {
            "current_password": "Testpass123!",
            "new_password": "BrandNewSecurePass123!",
            "re_new_password": "BrandNewSecurePass123!",
        }
        res = auth_client.post(SET_PASSWORD_URL, payload)
        assert res.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.check_password("BrandNewSecurePass123!") is True
        assert user.check_password("Testpass123!") is False
