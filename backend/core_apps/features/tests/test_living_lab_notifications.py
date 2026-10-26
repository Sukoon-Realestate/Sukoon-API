"""Student planning updates preserve personal decisions and membership periods."""

from datetime import timedelta
from unittest.mock import patch
import pytest
from django.utils import timezone
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.notifications.models import DeviceToken, PushDelivery
from core_apps.notifications.services.push_delivery import dispatch
from . import test_living_lab as fixtures

pytestmark = pytest.mark.django_db
rental_participants = fixtures.rental_participants
lab_capability = fixtures.lab_capability
context = fixtures.context
SEND = "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device"


def test_updates_commit_once_and_old_notice_opens_current_state(context):
    owner, admin, member, _, _, _ = context
    lab = fixtures.ready(context)
    events = PlanningEvent.objects.filter(destination__event_kind="living_lab_updated")
    assert events.count() == 2  # Create and aggregate result, no private-input notices.
    first = events.order_by("created_at").first()
    body = fixtures.command(lab["revision"])
    closed = fixtures.post(admin, f"living-labs/{lab['id']}/close/", body).data[
        "resource"
    ]
    assert closed["status"] == "closed"
    assert (
        fixtures.post(admin, f"living-labs/{lab['id']}/close/", body).data["resource"]
        == closed
    )
    assert events.count() == 3
    assert first.destination["target_id"] == lab["id"]
    current = fixtures.read(member, lab)
    assert current["status"] == "closed"
    assert [row["change"] for row in current["public_history"]] == [
        "closed",
        "result_updated",
        "created",
    ]
    assert not events.filter(recipient=owner).exists()
    assert "123456789" not in str(list(events.values("destination")))


def test_individual_accept_or_reject_not_disclosed_by_event(context):
    _, admin, member, _, _, _ = context
    lab = fixtures.ready(context)
    before = PlanningEvent.objects.count()
    lab = fixtures.respond(member, lab, "reject")
    assert PlanningEvent.objects.count() == before
    lab = fixtures.respond(member, lab)
    assert PlanningEvent.objects.count() == before
    lab = fixtures.respond(admin, lab)
    assert lab["status"] == "agreed"
    event = PlanningEvent.objects.get(destination__change="agreed")
    assert event.recipient == member
    assert set(event.destination) == {
        "schema_version",
        "action_type",
        "event_kind",
        "target_id",
        "group_id",
        "revision",
        "change",
        "workspace",
    }
    assert not lab["handoff_proposal_id"] and not lab["handoff_application_id"]


@pytest.mark.parametrize("change", ["leave", "rejoin", "wrong_group"])
def test_push_retry_checks_exact_membership_period(context, change):
    _, _, member, _, group, _ = context
    fixtures.create_lab(context)
    DeviceToken.objects.create(user=member, token="synthetic-lab-device")
    assert deliver_planning_events() == 1
    with patch(SEND, return_value=False):
        assert dispatch() == 0
    if change == "wrong_group":
        event = PlanningEvent.objects.get()
        event.destination["group_id"] = "wrong-group"
        event.save()
    else:
        group.memberships.filter(user=member).update(
            **({"status": "left"} if change == "leave" else {"joined_revision": 9})
        )
    PushDelivery.objects.update(next_attempt_at=timezone.now() - timedelta(seconds=1))
    with patch(SEND) as send:
        assert dispatch() == 0
        send.assert_not_called()
    assert PushDelivery.objects.get().suppressed


def test_event_failure_rolls_back_lab_creation(context):
    from core_apps.features.living_lab_models import SharedLivingLab

    with patch(
        "core_apps.features.services.living_lab.notifications.PlanningEvent.objects.get_or_create",
        side_effect=RuntimeError("queue unavailable"),
    ):
        with pytest.raises(AssertionError):
            fixtures.create_lab(context)
    assert not SharedLivingLab.objects.exists()
