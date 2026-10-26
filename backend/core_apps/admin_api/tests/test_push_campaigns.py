import uuid
from datetime import timedelta
from unittest.mock import patch
import pytest
from django.utils import timezone
from core_apps.admin_api.models import PushCampaign, CampaignDelivery
from core_apps.admin_api.services.push_campaigns import (
    preview,
    transition,
    dispatch,
    payload,
)
from core_apps.notifications.models import DeviceToken, Notification
from core_apps.profiles.models import UserSettings
from core_apps.common.idempotency import IdempotencyConflict

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def synthetic_credentials():
    with patch(
        "core_apps.admin_api.services.push_campaigns.FCMService.get_credentials",
        return_value=object(),
    ):
        yield


def target(user, token):
    UserSettings.objects.update_or_create(
        user=user, defaults={"promotions_and_updates": True}
    )
    from core_apps.notifications.services.preferences import touch

    touch(user, "individual")
    return DeviceToken.objects.create(user=user, token=token)


def confirm(actor, item):
    return transition(
        actor,
        item.id,
        {"expected_revision": item.revision, "preview_digest": item.preview_digest},
    )


def test_preview_and_confirmation_recovery_do_not_duplicate_sends(
    superuser, user, settings
):
    settings.ADMIN_CAMPAIGNS_ENABLED = True
    target(user, "synthetic-token")
    body = {
        "title": "QA only",
        "body": "Synthetic content",
        "request_key": str(uuid.uuid4()),
    }
    item = preview(superuser, body)
    assert preview(superuser, body).pk == item.pk
    assert not Notification.objects.exists()
    with pytest.raises(IdempotencyConflict):
        preview(superuser, {**body, "title": "Changed"})
    confirm(superuser, item)
    confirm(superuser, item)
    with patch(
        "core_apps.admin_api.services.push_campaigns.FCMService.send_push_to_device",
        return_value=True,
    ) as send:
        assert dispatch()["accepted_by_provider"] == 1
        assert dispatch()["accepted_by_provider"] == 0
        assert send.call_count == 1
    assert Notification.objects.count() == 1
    assert PushCampaign.objects.get().state == "complete"


def test_unknown_provider_result_and_interrupted_send_are_never_replayed(
    superuser, user, settings
):
    settings.ADMIN_CAMPAIGNS_ENABLED = True
    target(user, "unknown-token")
    item = preview(
        superuser, {"title": "QA", "body": "QA only", "request_key": str(uuid.uuid4())}
    )
    confirm(superuser, item)
    with patch(
        "core_apps.admin_api.services.push_campaigns.FCMService.send_push_to_device",
        return_value=False,
    ) as send:
        assert dispatch()["delivery_unknown"] == 1
        dispatch()
        assert send.call_count == 1
    row = CampaignDelivery.objects.get()
    row.state, row.attempt_started_at = "sending", timezone.now() - timedelta(minutes=6)
    row.save()
    with patch(
        "core_apps.admin_api.services.push_campaigns.FCMService.send_push_to_device"
    ) as send:
        dispatch()
        send.assert_not_called()
    row.refresh_from_db()
    assert row.state == "delivery_unknown"


def test_opt_out_registration_change_and_cancel_stop_remaining_delivery(
    superuser, user, another_user, settings
):
    settings.ADMIN_CAMPAIGNS_ENABLED = True
    target(user, "opt-out-token")
    device = target(another_user, "changed-token")
    item = preview(
        superuser, {"title": "QA", "body": "QA only", "request_key": str(uuid.uuid4())}
    )
    confirm(superuser, item)
    from core_apps.notifications.models import NotificationScopePreference

    NotificationScopePreference.objects.filter(user=user).update(
        promotions_and_updates=False
    )
    DeviceToken.objects.filter(pk=device.pk).update(token="replaced")
    with patch(
        "core_apps.admin_api.services.push_campaigns.FCMService.send_push_to_device"
    ) as send:
        assert dispatch()["skipped"] == 2
        send.assert_not_called()
    assert Notification.objects.filter(user=another_user).count() == 1
    assert not Notification.objects.filter(user=user).exists()
    item2 = preview(
        superuser, {"title": "QA", "body": "QA only", "request_key": str(uuid.uuid4())}
    )
    transition(
        superuser,
        item2.id,
        {"expected_revision": 1, "preview_digest": item2.preview_digest},
        cancel=True,
    )
    assert set(
        CampaignDelivery.objects.filter(recipient__campaign=item2).values_list(
            "state", flat=True
        )
    ) == {"cancelled"}


def test_confirmation_is_gated_and_permissions_are_fresh(superuser, user, settings):
    target(user, "gated-token")
    item = preview(
        superuser, {"title": "QA", "body": "QA only", "request_key": str(uuid.uuid4())}
    )
    assert payload(item)["can_confirm"] is False
    from rest_framework.exceptions import APIException, PermissionDenied

    with pytest.raises(APIException):
        confirm(superuser, item)
    superuser.is_active = False
    superuser.save()
    settings.ADMIN_CAMPAIGNS_ENABLED = True
    with pytest.raises(PermissionDenied):
        confirm(superuser, item)
    assert not Notification.objects.exists()


def test_known_credential_outage_preserves_queued_delivery(superuser, user, settings):
    settings.ADMIN_CAMPAIGNS_ENABLED = True
    target(user, "credential-outage")
    item = preview(
        superuser, {"title": "QA", "body": "QA only", "request_key": str(uuid.uuid4())}
    )
    confirm(superuser, item)
    with patch(
        "core_apps.admin_api.services.push_campaigns.FCMService.get_credentials",
        return_value=None,
    ), patch(
        "core_apps.admin_api.services.push_campaigns.FCMService.send_push_to_device"
    ) as send:
        assert dispatch() == {"provider_unavailable_before_send": 1}
        send.assert_not_called()
    assert CampaignDelivery.objects.get().state == "queued"
    assert Notification.objects.count() == 1
