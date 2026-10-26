from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.admin_api.models import StaffProfile
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.notifications.models import DeviceToken, Notification
from core_apps.notifications.services.fcm_service import FCMService
from core_apps.support.models import TicketMessage
from core_apps.support.services import create_ticket
from core_apps.support.services.staff_replies import reply_as_staff

pytestmark = pytest.mark.django_db


@pytest.fixture
def inquiry(user, another_user):
    StaffProfile.objects.create(user=another_user, role_name="support")
    ticket = create_ticket(
        user,
        "tenant",
        "payment",
        "Private inquiry",
        "Private bank information must stay in the ticket.",
    )
    return ticket, another_user


def reply(ticket, operator, **overrides):
    return reply_as_staff(
        **{
            "user": operator,
            "ticket_id": ticket.id,
            "body": "Sensitive advice; refund is still pending.",
            "expected_revision": 1,
            "request_key": "original-reply",
            **overrides,
        }
    )


def test_staff_reply_has_one_durable_generic_event_and_no_financial_effect(
    inquiry, monkeypatch
):
    ticket, operator = inquiry
    from core_apps.notifications.models import PushDelivery
    from core_apps.notifications.services.push_delivery import dispatch

    first = reply(ticket, operator)
    assert reply(ticket, operator)[:2] == first[:2]
    assert first[0]["effect"] == "advice_only"
    ticket.refresh_from_db()
    assert ticket.revision == 2 and ticket.status == "in_progress"
    assert TicketMessage.objects.filter(ticket=ticket, sender="support").count() == 1
    event = PlanningEvent.objects.get(recipient=ticket.user)
    assert event.destination["action_type"] == "open_support_ticket"
    assert "Sensitive" not in str(event.destination)
    DeviceToken.objects.create(user=ticket.user, token="disposable-device")
    monkeypatch.setattr(FCMService, "send_push_to_device", lambda **kwargs: False)
    assert deliver_planning_events() == 1
    assert dispatch() == 0
    event.refresh_from_db()
    assert event.delivered_at is not None and event.notification_id is not None
    assert event.provider_accepted_at is None
    assert Notification.objects.filter(user=ticket.user).count() == 1
    assert "Sensitive" not in event.notification.body
    PushDelivery.objects.filter(notification=event.notification).update(
        next_attempt_at=timezone.now() - timedelta(minutes=3)
    )
    monkeypatch.setattr(FCMService, "send_push_to_device", lambda **kwargs: True)
    assert dispatch() == 1
    assert dispatch() == 0
    assert deliver_planning_events() == 0
    assert Notification.objects.filter(user=ticket.user).count() == 1


def test_staff_reply_rechecks_authority_revision_and_independence(inquiry, user):
    ticket, operator = inquiry
    with pytest.raises(PermissionDenied):
        reply(ticket, user)
    StaffProfile.objects.create(user=user, role_name="support")
    with pytest.raises(PermissionDenied):
        reply(ticket, user)
    with pytest.raises(RentalConflict):
        reply(ticket, operator, expected_revision=99)
    operator.staff_profile.is_active = False
    operator.staff_profile.save()
    with pytest.raises(PermissionDenied):
        reply(ticket, operator)
    assert TicketMessage.objects.filter(sender="support").count() == 0
    assert not PlanningEvent.objects.exists()
