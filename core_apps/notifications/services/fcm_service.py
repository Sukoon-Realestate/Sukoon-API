import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import requests

from core_apps.notifications.models import DeviceToken

logger = logging.getLogger(__name__)

FCM_SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]


class FCMService:
    """
    Service for dispatching push notifications via Firebase Cloud Messaging HTTP v1 API.
    """

    _credentials = None

    @classmethod
    def get_credentials(cls) -> Optional[service_account.Credentials]:
        """
        Loads and caches Google service account credentials for FCM v1.
        Supports:
        1. FIREBASE_CREDENTIALS_JSON (raw JSON string in .env)
        2. Individual env vars: FIREBASE_CLIENT_EMAIL + FIREBASE_PRIVATE_KEY + FIREBASE_PROJECT_ID
        3. FIREBASE_CREDENTIALS_FILE (path to JSON file)
        """
        try:
            if cls._credentials is None:
                # 1. Check raw JSON env variable
                raw_json = getattr(settings, "FIREBASE_CREDENTIALS_JSON", None)
                if raw_json and raw_json.strip():
                    info_dict = json.loads(raw_json)
                    cls._credentials = service_account.Credentials.from_service_account_info(
                        info_dict, scopes=FCM_SCOPES
                    )
                # 2. Check individual env variables
                elif getattr(settings, "FIREBASE_PRIVATE_KEY", None) and getattr(
                    settings, "FIREBASE_CLIENT_EMAIL", None
                ):
                    private_key = settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n")
                    info_dict = {
                        "type": "service_account",
                        "project_id": getattr(settings, "FIREBASE_PROJECT_ID", "sokoun-99c7b"),
                        "private_key": private_key,
                        "client_email": settings.FIREBASE_CLIENT_EMAIL,
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                    cls._credentials = service_account.Credentials.from_service_account_info(
                        info_dict, scopes=FCM_SCOPES
                    )
                # 3. Fallback to file path
                else:
                    credentials_file = getattr(settings, "FIREBASE_CREDENTIALS_FILE", None)
                    if credentials_file and Path(credentials_file).is_file():
                        cls._credentials = (
                            service_account.Credentials.from_service_account_file(
                                credentials_file, scopes=FCM_SCOPES
                            )
                        )
                    else:
                        logger.warning("No Firebase credentials found in env or file.")
                        return None

            if cls._credentials and not cls._credentials.valid:
                cls._credentials.refresh(Request())
            return cls._credentials
        except Exception as exc:
            logger.error("Failed to load or refresh FCM credentials: %s", exc)
            return None

    @classmethod
    def get_project_id(cls) -> Optional[str]:
        """
        Retrieves project_id from settings, raw JSON, or service account file.
        """
        project_id = getattr(settings, "FIREBASE_PROJECT_ID", None)
        if project_id:
            return project_id

        raw_json = getattr(settings, "FIREBASE_CREDENTIALS_JSON", None)
        if raw_json and raw_json.strip():
            try:
                return json.loads(raw_json).get("project_id")
            except Exception:
                pass

        credentials_file = getattr(settings, "FIREBASE_CREDENTIALS_FILE", None)
        if credentials_file and Path(credentials_file).is_file():
            try:
                with open(credentials_file, "r", encoding="utf-8") as f:
                    return json.load(f).get("project_id")
            except Exception:
                pass
        return "sokoun-99c7b"

    @classmethod
    def should_send_to_user(cls, user: Any, notification_type: str) -> bool:
        """
        Checks user notification preferences before sending push notification.
        """
        try:
            from core_apps.profiles.models import UserSettings
            user_settings = UserSettings.objects.filter(user=user).first()
        except Exception:
            user_settings = getattr(user, "settings", None)

        if not user_settings:
            return True

        if notification_type in [
            "visit_request",
            "visit_accepted",
            "visit_rejected",
            "visit_review",
        ]:
            return getattr(user_settings, "visit_notifications", True)

        if notification_type in ["new_message"]:
            return getattr(user_settings, "owner_messages", True)

        if notification_type in [
            "property_update",
            "property_verified",
            "property_views",
            "daily_bump",
        ]:
            return getattr(user_settings, "property_updates", False)

        if notification_type in ["new_property"]:
            return getattr(user_settings, "property_updates", False) or getattr(
                user_settings, "new_properties_in_area", True
            )

        if notification_type in ["security_alert"]:
            return getattr(user_settings, "security_alerts", True)

        if notification_type in ["promotion"]:
            return getattr(user_settings, "promotions_and_updates", False)

        return True

    @classmethod
    def send_push_to_device(
        cls,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
        credentials: Optional[service_account.Credentials] = None,
    ) -> bool:
        """
        Sends a single push notification to a device token using FCM v1 HTTP API.
        """
        creds = credentials or cls.get_credentials()
        proj_id = project_id or cls.get_project_id()

        if not creds or not proj_id:
            logger.warning(
                "FCM push aborted: missing credentials or project ID (project_id=%s)",
                proj_id,
            )
            return False

        if not creds.valid:
            try:
                creds.refresh(Request())
            except Exception as exc:
                logger.error("Failed to refresh FCM access token: %s", exc)
                return False

        url = f"https://fcm.googleapis.com/v1/projects/{proj_id}/messages:send"
        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json; UTF-8",
        }

        # * Convert all data values to strings per FCM specification
        formatted_data = {}
        if data:
            for k, v in data.items():
                formatted_data[str(k)] = json.dumps(v) if isinstance(v, (dict, list)) else str(v)

        message_payload: Dict[str, Any] = {
            "message": {
                "token": token,
                "notification": {
                    "title": title,
                    "body": body,
                },
            }
        }
        if formatted_data:
            message_payload["message"]["data"] = formatted_data

        try:
            response = requests.post(url, headers=headers, json=message_payload, timeout=10)
            if response.status_code == 200:
                return True

            # ! Token is unregistered or invalid, deactivate it
            if response.status_code in (400, 404, 410):
                resp_text = response.text
                if (
                    "UNREGISTERED" in resp_text
                    or "NOT_FOUND" in resp_text
                    or "INVALID_ARGUMENT" in resp_text
                ):
                    DeviceToken.objects.filter(token=token).update(is_active=False)
                    logger.warning("Deactivated invalid FCM token: %s", token[:12])

            logger.error(
                "FCM send failed: HTTP %s - %s", response.status_code, response.text
            )
            return False
        except Exception as exc:
            logger.error("Exception occurred while sending FCM push: %s", exc)
            return False

    @classmethod
    def send_push_to_user(
        cls,
        user: Any,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        notification_type: str = "general",
    ) -> int:
        """
        Sends push notification to all active devices of the user,
        respecting user settings preferences.
        Returns the count of successfully delivered push messages.
        """
        if not cls.should_send_to_user(user, notification_type):
            return 0

        active_tokens = list(
            DeviceToken.objects.filter(user=user, is_active=True).values_list(
                "token", flat=True
            )
        )
        if not active_tokens:
            return 0

        creds = cls.get_credentials()
        proj_id = cls.get_project_id()

        sent_count = 0
        for token in active_tokens:
            success = cls.send_push_to_device(
                token=token,
                title=title,
                body=body,
                data=data,
                project_id=proj_id,
                credentials=creds,
            )
            if success:
                sent_count += 1

        return sent_count
