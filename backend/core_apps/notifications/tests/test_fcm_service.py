from unittest.mock import MagicMock, patch
import pytest

from core_apps.notifications.models import DeviceToken
from core_apps.notifications.services import FCMService
from core_apps.profiles.models import UserSettings


@pytest.mark.django_db
class TestFCMService:
    def test_should_send_to_user_respects_settings(self, user):
        settings_obj, _ = UserSettings.objects.get_or_create(user=user)

        # Visit notifications enabled
        settings_obj.visit_notifications = True
        settings_obj.save()
        assert FCMService.should_send_to_user(user, "visit_accepted") is True

        # Visit notifications disabled
        settings_obj.visit_notifications = False
        settings_obj.save()
        assert FCMService.should_send_to_user(user, "visit_accepted") is False

        # Property updates disabled by default
        settings_obj.property_updates = False
        settings_obj.save()
        assert FCMService.should_send_to_user(user, "property_update") is False

        # Property updates enabled
        settings_obj.property_updates = True
        settings_obj.save()
        assert FCMService.should_send_to_user(user, "property_update") is True

        # Security alerts disabled
        settings_obj.security_alerts = False
        settings_obj.save()
        assert FCMService.should_send_to_user(user, "security_alert") is False

        # Promotions disabled
        settings_obj.promotions_and_updates = False
        settings_obj.save()
        assert FCMService.should_send_to_user(user, "promotion") is False

    @patch("google.oauth2.service_account.Credentials.from_service_account_info")
    def test_get_credentials_from_individual_env_vars(self, mock_from_info, settings):
        settings.FIREBASE_PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----"
        settings.FIREBASE_CLIENT_EMAIL = "test@sokoun-99c7b.iam.gserviceaccount.com"
        settings.FIREBASE_PROJECT_ID = "sokoun-99c7b"
        settings.FIREBASE_CREDENTIALS_JSON = None
        settings.FIREBASE_CREDENTIALS_FILE = None

        FCMService._credentials = None
        creds = FCMService.get_credentials()
        mock_from_info.assert_called_once()
        call_dict = mock_from_info.call_args[0][0]
        assert call_dict["client_email"] == "test@sokoun-99c7b.iam.gserviceaccount.com"
        assert "\n" in call_dict["private_key"]

    @patch("requests.post")
    def test_send_push_to_device_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.token = "mock_bearer_token"

        success = FCMService.send_push_to_device(
            token="device_token_abc",
            title="إشعار جديد",
            body="محتوى الإشعار",
            data={"key": "value"},
            project_id="sokoun-99c7b",
            credentials=mock_creds,
        )
        assert success is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "sokoun-99c7b" in args[0]
        assert kwargs["json"]["message"]["notification"]["title"] == "إشعار جديد"

    @patch("requests.post")
    def test_send_push_to_device_deactivates_unregistered_token(self, mock_post, user):
        token_str = "unregistered_token_12345"
        device = DeviceToken.objects.create(
            user=user, token=token_str, is_active=True
        )

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": {"status": "NOT_FOUND", "message": "Requested entity was not found."}}'
        mock_post.return_value = mock_response

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.token = "mock_token"

        success = FCMService.send_push_to_device(
            token=token_str,
            title="Title",
            body="Body",
            project_id="sokoun-99c7b",
            credentials=mock_creds,
        )
        assert success is False
        device.refresh_from_db()
        assert device.is_active is False

    @patch.object(FCMService, "send_push_to_device", return_value=True)
    def test_send_push_to_user_skips_when_settings_disabled(self, mock_send_device, user):
        settings_obj, _ = UserSettings.objects.get_or_create(user=user)
        settings_obj.visit_notifications = False
        settings_obj.save()

        DeviceToken.objects.create(user=user, token="tok_1", is_active=True)

        sent = FCMService.send_push_to_user(
            user=user,
            title="Title",
            body="Body",
            notification_type="visit_accepted",
        )
        assert sent == 0
        mock_send_device.assert_not_called()

    @patch.object(FCMService, "get_credentials")
    @patch.object(FCMService, "get_project_id", return_value="sokoun-99c7b")
    @patch.object(FCMService, "send_push_to_device", return_value=True)
    def test_send_push_to_user_delivers_to_active_tokens(
        self, mock_send_device, mock_project_id, mock_creds, user
    ):
        settings_obj, _ = UserSettings.objects.get_or_create(user=user)
        settings_obj.visit_notifications = True
        settings_obj.save()

        DeviceToken.objects.create(user=user, token="tok_active_1", is_active=True)
        DeviceToken.objects.create(user=user, token="tok_active_2", is_active=True)
        DeviceToken.objects.create(user=user, token="tok_inactive", is_active=False)

        sent = FCMService.send_push_to_user(
            user=user,
            title="Title",
            body="Body",
            notification_type="visit_accepted",
        )
        assert sent == 2
        assert mock_send_device.call_count == 2
