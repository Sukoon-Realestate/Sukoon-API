import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestCompleteRegisterAPI:
    def test_complete_register_updates_national_id_and_returns_pending(
        self, auth_client, user
    ):
        url = reverse("complete-register")
        payload = {
            "national_id": "29505151234567",
        }
        res = auth_client.post(url, payload, format="multipart")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["verification_status"] == "pending"
        assert "front_id_image" in data["missing_fields"]
        assert "back_id_image" in data["missing_fields"]
        assert data["registration_complete"] is False

        # Verify user profile was updated
        user.profile.refresh_from_db()
        assert user.profile.national_id == "29505151234567"

    def test_complete_register_with_all_documents(self, auth_client, user):
        url = reverse("complete-register")
        # Pre-set national id and face on profile
        user.profile.national_id = "29505151234567"
        user.profile.id_face = "https://media.example.com/id_face.jpg"
        user.profile.id_back = "https://media.example.com/id_back.jpg"
        user.profile.save()

        payload = {
            "national_id": "29505151234567",
        }
        res = auth_client.post(url, payload, format="multipart")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["registration_complete"] is True
        assert data["missing_fields"] == []
        assert data["verification_status"] == "pending"

    def test_complete_register_invalid_national_id_length(self, auth_client, user):
        url = reverse("complete-register")
        payload = {
            "national_id": "12345",
        }
        res = auth_client.post(url, payload, format="multipart")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_complete_register_returns_401(self, api_client):
        url = reverse("complete-register")
        res = api_client.post(url, {"national_id": "29505151234567"}, format="multipart")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
