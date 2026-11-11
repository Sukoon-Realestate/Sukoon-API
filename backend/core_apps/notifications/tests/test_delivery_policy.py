from datetime import datetime, timedelta, timezone as utc_timezone
from zoneinfo import ZoneInfo
from unittest.mock import patch
from uuid import uuid4
import json
import os
from pathlib import Path

import pytest
from django.urls import reverse
from core_apps.notifications.models import (
    DeviceToken,
    Notification,
    PushDelivery,
    NotificationDeliveryPolicy,
    NotificationDailyDigest,
    NotificationDigestHold,
)
from core_apps.notifications.services.delivery_policy import (
    CATEGORIES,
    build_digests,
    quiet_until,
    next_digest,
)
from core_apps.notifications.services.notification_service import NotificationService
from core_apps.notifications.services.push_delivery import dispatch
from core_apps.notifications.services.fcm_service import FCMService
from core_apps.profiles.tests.test_identity_expiry import card

pytestmark = pytest.mark.django_db


def policy(user, mode="daily", **kwargs):
    return NotificationDeliveryPolicy.objects.create(
        user=user, modes={category: mode for category in CATEGORIES}, **kwargs
    )


def notice(user, **kwargs):
    return NotificationService.create_notification(
        user=user,
        title="Synthetic listing update",
        notification_type="new_property",
        data={"workspace": "individual"},
        **kwargs
    )


def test_policy_default_is_immediate_private_cas_and_idempotent(api_client, user, another_user):
    api_client.force_authenticate(user)
    url = reverse("notification-delivery-policy")
    response = api_client.get(url)
    assert response.status_code == 200 and set(response.data["modes"].values()) == {"immediate"}
    assert response["Cache-Control"] == "private, no-store"
    body = {
        "expected_revision": 0,
        "timezone": "Africa/Cairo",
        "modes": {key: "daily" for key in CATEGORIES},
        "quiet_start": 1320,
        "quiet_end": 480,
    }
    key = str(uuid4())

    def save(payload, identity):
        return api_client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=identity)

    first = save(body, key)
    assert first.status_code == 200, first.data
    assert save(body, key).data == first.data
    assert save(body, str(uuid4())).status_code == 409
    assert save({**body, "timezone": "invalid-zone"}, str(uuid4())).status_code == 400
    assert save({**body, "modes": {"promotion": "daily"}}, str(uuid4())).status_code == 400
    assert save({**body, "quiet_end": 1320}, str(uuid4())).status_code == 400
    exported = os.environ.get("MVP_FIXTURE_DIR")
    if exported:
        (Path(exported) / "notification_delivery_policy.json").write_text(
            json.dumps(first.data), encoding="utf8"
        )
    api_client.force_authenticate(another_user)
    assert api_client.get(url).data["revision"] == 0


def test_ten_updates_become_one_durable_summary_and_never_replay_originals(user):
    DeviceToken.objects.create(user=user, token="mock-device")
    policy(user)
    before = datetime(2027, 1, 15, 12, tzinfo=ZoneInfo("Africa/Cairo"))
    after = before.replace(hour=19, minute=1)
    with patch("django.utils.timezone.now", return_value=before), patch.object(
        FCMService, "send_push_to_device", return_value=True
    ) as send:
        for _ in range(10):
            notice(user)
        assert dispatch() == 0 and send.call_count == 0
        assert Notification.objects.count() == 10  # In-app history is immediate.
        assert NotificationDigestHold.objects.count() == 10
        assert PushDelivery.objects.filter(attempts=0).count() == 10
    with patch("django.utils.timezone.now", return_value=after), patch.object(
        FCMService, "send_push_to_device", side_effect=[False, True]
    ) as send:
        assert build_digests() == 1 and build_digests() == 0
        assert NotificationDailyDigest.objects.count() == 1
        assert dispatch() == 0
        PushDelivery.objects.filter(notification__category="notification_summary").update(
            next_attempt_at=after
        )
        assert dispatch() == 1 and dispatch() == 0
        assert send.call_count == 2
        assert PushDelivery.objects.filter(suppressed=True).count() == 10


def test_quiet_hours_defer_without_spending_retry_budget_and_off_revokes(user):
    DeviceToken.objects.create(user=user, token="mock-device")
    item = policy(user, "immediate", quiet_start=22 * 60, quiet_end=8 * 60)
    now = datetime(2027, 1, 15, 23, tzinfo=ZoneInfo("Africa/Cairo"))
    with patch("django.utils.timezone.now", return_value=now), patch.object(
        FCMService, "send_push_to_device"
    ) as send:
        notification = notice(user)
        assert dispatch() == 0
        delivery = PushDelivery.objects.get(notification=notification)
        assert (
            delivery.attempts == 0
            and delivery.next_attempt_at.astimezone(ZoneInfo("Africa/Cairo")).hour == 8
        )
        item.modes["discovery"] = "off"
        item.save()
        PushDelivery.objects.update(next_attempt_at=now)
        assert dispatch() == 0 and PushDelivery.objects.get().suppressed
        send.assert_not_called()


def test_revoked_consent_before_summary_push_suppresses_without_removing_inbox(user):
    DeviceToken.objects.create(user=user, token="mock-device")
    item = policy(user)
    now = datetime(2027, 1, 15, 12, tzinfo=ZoneInfo("Africa/Cairo"))
    with patch("django.utils.timezone.now", return_value=now), patch.object(
        FCMService, "send_push_to_device"
    ):
        notice(user)
        dispatch()
    with patch("django.utils.timezone.now", return_value=now.replace(hour=20)), patch.object(
        FCMService, "send_push_to_device"
    ) as send:
        assert build_digests() == 1
        item.modes["discovery"] = "off"
        item.save()
        assert dispatch() == 0
        send.assert_not_called()
        assert Notification.objects.count() == 2


def test_security_is_never_reclassified_or_delayed_by_optional_policy(user):
    DeviceToken.objects.create(user=user, token="mock-device")
    policy(user, "off", quiet_start=22 * 60, quiet_end=8 * 60)
    now = datetime(2027, 1, 15, 23, tzinfo=ZoneInfo("Africa/Cairo"))
    with patch("django.utils.timezone.now", return_value=now), patch.object(
        FCMService, "send_push_to_device", return_value=True
    ) as send:
        NotificationService.create_notification(
            user=user, title="Account security", notification_type="security_alert"
        )
        assert dispatch() == 1 and send.call_count == 1
        assert not NotificationDigestHold.objects.exists()


def test_imminent_viewing_bypasses_digest_and_quiet_hours(user, another_user):
    from datetime import time
    from core_apps.properties.models import PropertyVisit
    from core_apps.properties.tests.test_views import _create_published_property

    DeviceToken.objects.create(user=user, token="mock-device")
    policy(user, quiet_start=12 * 60, quiet_end=18 * 60)
    now = datetime(2027, 1, 15, 14, tzinfo=ZoneInfo("Africa/Cairo"))
    prop = _create_published_property(owner=another_user, price=1000)
    visit = PropertyVisit.objects.create(
        property=prop, tenant=user, status="confirmed", visit_date=now.date(), visit_time=time(16)
    )
    with patch("django.utils.timezone.now", return_value=now), patch.object(
        FCMService, "send_push_to_device", return_value=True
    ):
        NotificationService.create_notification(
            user=user,
            title="Viewing time updated",
            notification_type="visit_accepted",
            data={"workspace": "individual", "visit_id": str(visit.id)},
        )
        assert dispatch() == 1
        assert not NotificationDigestHold.objects.exists()


def test_identity_reminder_cannot_be_delayed_beyond_document_expiry(user, card):
    from core_apps.profiles.models import IdentityDocumentExpiry
    from core_apps.profiles.identity_expiry import card_version, record_reminders
    from core_apps.features.services.planning_notifications_parts.deliver_planning_events import (
        deliver_planning_events,
    )

    DeviceToken.objects.create(user=user, token="mock-device")
    policy(user, quiet_start=10 * 60, quiet_end=9 * 60)
    now = datetime(2027, 1, 15, 20, tzinfo=ZoneInfo("Africa/Cairo"))
    IdentityDocumentExpiry.objects.create(
        profile=card,
        document_version=card_version(card),
        expires_on=now.date() + timedelta(days=1),
        reminder_days=[1],
    )
    with patch("django.utils.timezone.now", return_value=now), patch.object(
        FCMService, "send_push_to_device", return_value=True
    ):
        assert record_reminders() == 1
        assert deliver_planning_events(event_kinds=["identity_document_expiry"]) == 1
        assert dispatch() == 1
        assert not NotificationDigestHold.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_digest_workers_and_timezone_change_never_duplicate_summary(user):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import close_old_connections

    DeviceToken.objects.create(user=user, token="mock-device")
    item = policy(user)
    before = datetime(2027, 1, 15, 12, tzinfo=ZoneInfo("Africa/Cairo"))
    after = before.replace(hour=20)
    with patch("django.utils.timezone.now", return_value=before), patch.object(
        FCMService, "send_push_to_device"
    ):
        for _ in range(3):
            notice(user)
        dispatch()
    barrier = Barrier(2)

    def build(_):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return build_digests(now=after)
        finally:
            close_old_connections()

    with patch("django.utils.timezone.now", return_value=after):
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sum(pool.map(build, range(2))) == 1
        assert NotificationDailyDigest.objects.count() == 1
        with patch.object(FCMService, "send_push_to_device", side_effect=[False, True]) as send:
            assert dispatch() == 0
            item.timezone_name = "America/New_York"
            item.revision += 1
            item.save()
            assert build_digests() == 0
            PushDelivery.objects.filter(notification__category="notification_summary").update(
                next_attempt_at=after
            )
            assert dispatch() == 1 and send.call_count == 2
        assert NotificationDailyDigest.objects.count() == 1


def test_cairo_dst_gap_and_fold_resolve_to_real_future_instants(user):
    item = policy(user, quiet_start=22 * 60, quiet_end=0)
    # Cairo skips 00:00 at the start of summer time.
    now = datetime(2027, 4, 29, 23, 30, tzinfo=ZoneInfo("Africa/Cairo"))
    due = quiet_until(item, now)
    assert due > now.astimezone(utc_timezone.utc)
    assert due.astimezone(ZoneInfo("Africa/Cairo")).hour == 1
    first, day = next_digest(item, now)
    second, other_day = next_digest(item, now + timedelta(minutes=10))
    assert first == second and day == other_day


@pytest.mark.parametrize("valid_second", [True, False])
def test_digest_uses_any_currently_authorized_device(user, valid_second):
    from core_apps.users.models import AuthSession
    from core_apps.notifications.services.delivery_policy import summary_authorized

    now = datetime(2027, 1, 15, 12, tzinfo=ZoneInfo("Africa/Cairo"))
    user.requires_bound_session = True
    user.save(update_fields=["requires_bound_session"])
    expired = AuthSession.objects.create(
        user=user, security_epoch=user.security_epoch, expires_at=now + timedelta(hours=1)
    )
    active = AuthSession.objects.create(
        user=user,
        security_epoch=user.security_epoch,
        expires_at=now + timedelta(days=1) if valid_second else now - timedelta(seconds=1),
    )
    DeviceToken.objects.create(user=user, token="expired-first", auth_session=expired)
    DeviceToken.objects.create(user=user, token="second", auth_session=active)
    policy(user)
    with patch("django.utils.timezone.now", return_value=now):
        notification = notice(user)
        dispatch()
    after = now.replace(hour=20)
    with patch("django.utils.timezone.now", return_value=after), patch.object(
        FCMService, "send_push_to_device", return_value=True
    ) as send:
        assert build_digests() == int(valid_second)
        if valid_second:
            digest = NotificationDailyDigest.objects.get()
            assert summary_authorized(digest.notification)
            assert dispatch() == 1
            assert send.call_count == 1
            active.revoked_at = after
            active.save(update_fields=["revoked_at"])
            assert not summary_authorized(digest.notification)
        else:
            assert (
                NotificationDigestHold.objects.get(notification=notification).state == "suppressed"
            )
            send.assert_not_called()
