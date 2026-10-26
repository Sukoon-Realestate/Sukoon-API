"""Event delivery commits before provider IO and retries only an authorized notice."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch
import uuid
import pytest
from django.contrib.auth import get_user_model
from django.db import connections
from django.utils import timezone
from core_apps.features.models import SearchAlert
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.notifications.models import DeviceToken, Notification, PushDelivery
from core_apps.notifications.services.push_delivery import dispatch

pytestmark = pytest.mark.django_db
SEND = "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device"


@pytest.fixture
def event():
    user = get_user_model().objects.create_user(
        email="outbox@example.test", password="local"
    )
    alert = SearchAlert.objects.create(
        user=user, name="Private search", cadence="daily"
    )
    DeviceToken.objects.create(user=user, token="local-outbox-device")
    return PlanningEvent.objects.create(
        recipient=user,
        event_key="search-alert:local",
        destination={
            "action_type": "open_search_alert",
            "target_id": str(alert.id),
            "workspace": "student",
            "revision": alert.revision,
        },
    )


def test_bridge_rolls_back_notice_and_claim_when_queue_write_fails(event):
    with patch(
        "core_apps.notifications.services.push_delivery.queue_notification",
        side_effect=RuntimeError("queue write failed"),
    ):
        with pytest.raises(RuntimeError):
            deliver_planning_events()
    event.refresh_from_db()
    assert not event.delivered_at and not event.notification_id
    assert not Notification.objects.exists() and not PushDelivery.objects.exists()
    with patch(SEND) as send:
        assert deliver_planning_events() == 1
        assert deliver_planning_events() == 0
        send.assert_not_called()
    assert (
        Notification.objects.count()
        == PushDelivery.objects.count()
        == SearchAlert.objects.count()
        == 1
    )


@pytest.mark.parametrize(
    "change", ["disable", "delete", "revision", "target", "scope", "event_pointer"]
)
def test_retry_rechecks_source_and_exact_destination(event, change):
    deliver_planning_events()
    with patch(SEND, return_value=False):
        assert dispatch() == 0
    event.refresh_from_db()
    notice = event.notification
    if change == "disable":
        SearchAlert.objects.update(enabled=False)
    elif change == "delete":
        SearchAlert.objects.update(deleted_at=timezone.now())
    elif change == "revision":
        SearchAlert.objects.update(revision=2)
    elif change == "target":
        notice.data["target_id"] = "another-alert"
    elif change == "scope":
        notice.scope = "owner"
    else:
        notice.data["event_id"] = "invalid"
    notice.save()
    PushDelivery.objects.update(next_attempt_at=timezone.now() - timedelta(seconds=1))
    with patch(SEND) as send:
        assert dispatch() == 0
        send.assert_not_called()
    assert PushDelivery.objects.get().suppressed
    assert not event.provider_accepted_at
    assert Notification.objects.count() == SearchAlert.objects.count() == 1


def test_inactive_recipients_do_not_starve_active_events_or_delete_queue(event):
    inactive = get_user_model().objects.create_user(
        email="inactive@example.test", password="local", is_active=False
    )
    for index in range(101):
        PlanningEvent.objects.create(
            recipient=inactive,
            event_key=f"inactive:{index}",
            destination=event.destination,
        )
    PlanningEvent.objects.filter(recipient=inactive).update(
        created_at=timezone.now() - timedelta(days=1)
    )
    assert deliver_planning_events() == 1
    assert (
        PlanningEvent.objects.filter(
            recipient=inactive, delivered_at__isnull=True
        ).count()
        == 101
    )
    assert Notification.objects.count() == 1


@pytest.mark.parametrize("source", ["security", "planning"])
def test_event_id_alone_does_not_reclassify_an_account_notice(event, source):
    from core_apps.notifications.services.notification_service import (
        NotificationService,
    )

    notice = NotificationService.create_notification(
        user=event.recipient,
        title="Account update",
        notification_type="security_alert",
        data={
            "scope": "account",
            "event_id": str(uuid.uuid4()),
            "event_source": source,
        },
    )
    with patch(SEND, return_value=True) as send:
        assert dispatch() == (1 if source == "security" else 0)
        assert send.call_count == (1 if source == "security" else 0)
    assert PushDelivery.objects.get(notification=notice).suppressed == (
        source == "planning"
    )


@pytest.mark.django_db(transaction=True)
def test_two_workers_keep_one_receipt_and_device_job(event):
    def run(_):
        connections.close_all()
        try:
            return deliver_planning_events()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(run, range(2))) == 1
    assert (
        Notification.objects.count()
        == PushDelivery.objects.count()
        == SearchAlert.objects.count()
        == 1
    )
