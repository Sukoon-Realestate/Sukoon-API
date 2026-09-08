import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from core_apps.profiles.models import UserSettings

User = get_user_model()
SETTINGS_URL = reverse("user-settings")


@pytest.mark.django_db
class TestUserSettingsAPI:
    """Tests for 'الإعدادات والخصوصية' (Settings & Privacy) API."""

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(SETTINGS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_settings_default_values(self, auth_client, user):
        response = auth_client.get(SETTINGS_URL)
        assert response.status_code == status.HTTP_200_OK

        data = response.data
        # * Notifications defaults
        assert data["visit_notifications"] is True
        assert data["new_properties_in_area"] is True
        assert data["owner_messages"] is True
        assert data["promotions_and_updates"] is False

        # * Privacy defaults
        assert data["always_hide_mobile_number"] is True
        assert data["always_hide_mobile_number_locked"] is True
        assert data["share_location_for_search"] is True
        assert data["show_profile_in_search"] is False

        # * UI Sections structure check
        assert "sections" in data
        assert "notifications" in data["sections"]
        assert "privacy" in data["sections"]
        assert data["sections"]["notifications"]["title"] == "الإشعارات"
        assert data["sections"]["privacy"]["title"] == "الخصوصية"

    def test_patch_settings_flat_payload(self, auth_client, user):
        payload = {
            "visit_notifications": False,
            "promotions_and_updates": True,
            "share_location_for_search": False,
        }
        response = auth_client.patch(SETTINGS_URL, payload, format="json")
        assert response.status_code == status.HTTP_200_OK

        data = response.data
        assert data["visit_notifications"] is False
        assert data["promotions_and_updates"] is True
        assert data["share_location_for_search"] is False
        # Unchanged fields remain intact
        assert data["new_properties_in_area"] is True
        assert data["owner_messages"] is True

        # Check DB persistence
        settings_obj = UserSettings.objects.get(user=user)
        assert settings_obj.visit_notifications is False
        assert settings_obj.promotions_and_updates is True
        assert settings_obj.share_location_for_search is False

    def test_patch_settings_nested_payload(self, auth_client, user):
        payload = {
            "notifications": {
                "owner_messages": False,
            },
            "privacy": {
                "show_profile_in_search": True,
            },
        }
        response = auth_client.patch(SETTINGS_URL, payload, format="json")
        assert response.status_code == status.HTTP_200_OK

        data = response.data
        assert data["owner_messages"] is False
        assert data["show_profile_in_search"] is True

        settings_obj = UserSettings.objects.get(user=user)
        assert settings_obj.owner_messages is False
        assert settings_obj.show_profile_in_search is True

    def test_always_hide_mobile_number_cannot_be_disabled(self, auth_client, user):
        payload = {
            "always_hide_mobile_number": False,
        }
        response = auth_client.patch(SETTINGS_URL, payload, format="json")
        assert response.status_code == status.HTTP_200_OK

        data = response.data
        assert data["always_hide_mobile_number"] is True

        settings_obj = UserSettings.objects.get(user=user)
        assert settings_obj.always_hide_mobile_number is True

    def test_put_settings_full_update(self, auth_client, user):
        payload = {
            "visit_notifications": False,
            "new_properties_in_area": False,
            "owner_messages": False,
            "promotions_and_updates": True,
            "share_location_for_search": False,
            "show_profile_in_search": True,
        }
        response = auth_client.put(SETTINGS_URL, payload, format="json")
        assert response.status_code == status.HTTP_200_OK

        data = response.data
        assert data["visit_notifications"] is False
        assert data["new_properties_in_area"] is False
        assert data["owner_messages"] is False
        assert data["promotions_and_updates"] is True
        assert data["share_location_for_search"] is False
        assert data["show_profile_in_search"] is True
        assert data["always_hide_mobile_number"] is True

    def test_user_creation_signal_creates_settings(self, db):
        new_user = User.objects.create_user(
            email="signal_settings@example.com",
            first_name="Settings",
            last_name="Tester",
            password="Password123!",
        )
        assert hasattr(new_user, "settings")
        assert new_user.settings.visit_notifications is True
        assert str(new_user.settings) == f"Settings for {new_user.email}"
