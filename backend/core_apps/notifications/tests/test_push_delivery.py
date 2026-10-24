from datetime import timedelta
from unittest.mock import patch, MagicMock
import pytest
from django.utils import timezone
from core_apps.notifications.models import DeviceToken, PushDelivery
from core_apps.notifications.services.notification_service import NotificationService
from core_apps.notifications.services.push_delivery import dispatch
from core_apps.notifications.services.fcm_service import FCMService
from core_apps.users.models import AuthSession
from core_apps.users.services.sessions import issue_refresh

pytestmark = pytest.mark.django_db


def create(user):
    session = AuthSession.objects.get(id=issue_refresh(user)["session_id"])
    device = DeviceToken.objects.create(
        user=user, token="synthetic-device", language="en", auth_session=session
    )
    notice = NotificationService.create_notification(
        user=user, title="Private title", body="Private details"
    )
    return device, notice


def test_durable_push_retries_without_duplicate_inbox(user):
    device, notice = create(user)
    assert PushDelivery.objects.filter(notification=notice).count() == 1
    with patch.object(
        FCMService, "send_push_to_device", side_effect=[False, True]
    ) as send:
        assert dispatch() == 0
        assert dispatch() == 0
        PushDelivery.objects.update(
            next_attempt_at=timezone.now() - timedelta(seconds=1)
        )
        assert dispatch() == 1
        assert dispatch() == 0
        assert send.call_count == 2
        assert send.call_args.kwargs["language"] == "en"
    assert notice.__class__.objects.filter(pk=notice.pk).count() == 1


def test_session_revocation_before_dispatch_suppresses_push(user):
    device, notice = create(user)
    AuthSession.objects.filter(pk=device.auth_session_id).update(
        revoked_at=timezone.now()
    )
    with patch.object(FCMService, "send_push_to_device") as send:
        assert dispatch() == 0
        send.assert_not_called()
    assert PushDelivery.objects.get(notification=notice).suppressed


def test_invalid_request_does_not_deactivate_valid_registration(user):
    device, _ = create(user)
    with patch(
        "requests.post",
        return_value=MagicMock(status_code=400, text="INVALID_ARGUMENT"),
    ):
        assert not FCMService.send_push_to_device(
            token=device.token,
            title="",
            body="",
            credentials=MagicMock(valid=True, token="synthetic"),
            project_id="test",
        )
    device.refresh_from_db()
    assert device.is_active


def test_android_payload_has_heads_up_channel_and_localized_private_preview():
    with patch("requests.post", return_value=MagicMock(status_code=200)) as send:
        assert FCMService.send_push_to_device(
            token="synthetic",
            title="Private",
            body="Private",
            language="en",
            credentials=MagicMock(valid=True, token="synthetic"),
            project_id="test",
        )
    message = send.call_args.kwargs["json"]["message"]
    assert message["android"]["priority"] == "HIGH"
    assert message["android"]["notification"]["channel_id"] == "high_importance_channel"
    assert message["notification"]["title"] == "Sokoun"
    assert "Private" not in str(message)


def test_malformed_chat_identity_does_not_interrupt_other_deliveries(user):
    _, invalid = create(user)
    invalid.notification_type = "new_message"
    invalid.data = {"conversation_id": "invalid-identity"}
    invalid.save(update_fields=["notification_type", "data"])
    valid = NotificationService.create_notification(
        user=user, title="Next", body="Private"
    )
    with patch.object(FCMService, "send_push_to_device", return_value=True) as send:
        assert dispatch() == 1
        assert send.call_count == 1
    assert PushDelivery.objects.get(notification=invalid).suppressed
    assert PushDelivery.objects.get(notification=valid).accepted_at
