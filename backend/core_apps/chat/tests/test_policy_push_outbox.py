"""Delivery retries do not repeat moderation judgments or alter enforcement."""

from datetime import timedelta
from unittest.mock import patch
import pytest
from django.utils import timezone
from core_apps.chat.tests import test_rental_moderation as moderation
from core_apps.chat.models import ChatModerationCase, AccountRestriction
from core_apps.chat.moderation.notifications import deliver_pending
from core_apps.notifications.models import DeviceToken, PushDelivery
from core_apps.notifications.services.push_delivery import dispatch

pytestmark = pytest.mark.django_db
rental_chat = moderation.rental_chat
SEND = "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device"


def policy_notice(rental_chat):
    chat, user, other = rental_chat
    DeviceToken.objects.create(user=user, token="policy-qa-device")
    message = moderation.send(chat, user)
    moderation.run()
    case = ChatModerationCase.objects.get()
    assert case.notification and message.content not in str(case.notification.data)
    assert case.notification.scope == "account"
    return case


def test_policy_retry_is_durable_and_does_not_repeat_the_judgment(rental_chat):
    case = policy_notice(rental_chat)
    revision, state = case.revision, case.state
    with patch(SEND) as send:
        deliver_pending()
        deliver_pending()
        send.assert_not_called()
    job = PushDelivery.objects.get(notification=case.notification)
    with patch(SEND, side_effect=[False, True]) as send:
        assert dispatch() == 0
        PushDelivery.objects.filter(pk=job.pk).update(
            next_attempt_at=timezone.now() - timedelta(seconds=1)
        )
        assert dispatch() == 1
        assert dispatch() == 0
        assert {call.kwargs["data"]["case_id"] for call in send.call_args_list} == {
            str(case.id)
        }
    case.refresh_from_db()
    assert case.revision == revision and case.state == state
    assert not AccountRestriction.objects.exists()
    assert ChatModerationCase.objects.count() == 1


def test_policy_resolution_before_retry_suppresses_the_old_notice(rental_chat):
    case = policy_notice(rental_chat)
    deliver_pending()
    with patch(SEND, return_value=False):
        assert dispatch() == 0
    ChatModerationCase.objects.filter(pk=case.pk).update(resolved_at=timezone.now())
    PushDelivery.objects.update(next_attempt_at=timezone.now() - timedelta(seconds=1))
    with patch(SEND) as send:
        assert dispatch() == 0
        send.assert_not_called()
    assert PushDelivery.objects.get(notification=case.notification).suppressed


def test_queue_failure_does_not_consume_the_policy_notice_claim(rental_chat):
    case = policy_notice(rental_chat)
    with patch(
        "core_apps.notifications.services.push_delivery.queue_notification",
        side_effect=RuntimeError("queue failed"),
    ):
        with pytest.raises(RuntimeError):
            deliver_pending()
    case.refresh_from_db()
    assert case.push_claimed_at is None
    assert not PushDelivery.objects.filter(notification=case.notification).exists()
    deliver_pending()
    assert PushDelivery.objects.filter(notification=case.notification).count() == 1


def test_previously_claimed_notice_is_not_backfilled(rental_chat):
    case = policy_notice(rental_chat)
    case.push_claimed_at = timezone.now() - timedelta(days=1)
    case.save(update_fields=["push_claimed_at"])
    deliver_pending()
    assert not PushDelivery.objects.filter(notification=case.notification).exists()
