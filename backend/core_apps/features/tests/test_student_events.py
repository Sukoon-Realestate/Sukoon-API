from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

import pytest
from django.db import transaction, connections
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import NotFound

from core_apps.features.models import AcademicHousingPlan, Lease
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.features.services.student_housing.notifications import authorize
from core_apps.features.services.student_housing.access import actions
from core_apps.features.tests import test_student_housing as fixtures
from core_apps.features.tests.test_rental_lifecycle import command
from core_apps.notifications.models import DeviceToken, Notification, PushDelivery
from core_apps.notifications.services.push_delivery import dispatch

rental_participants = fixtures.rental_participants
student_capabilities = fixtures.student_capabilities
group = fixtures.group
pytestmark = pytest.mark.django_db
SEND = "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device"


def create(rental_participants, group):
    _, tenant, member, prop, _ = rental_participants
    return fixtures.create_plan(tenant, prop, group=group, people=[tenant, member])


def test_command_and_event_share_receipt_and_rollback(rental_participants, group):
    owner, tenant, member, prop, _ = rental_participants
    body = fixtures.plan_body(tenant, prop, group=group, people=[tenant, member])
    first = fixtures.post(tenant, "academic-plans/", body, 201)
    replay = fixtures.post(tenant, "academic-plans/", body, 201)
    assert first.data == replay.data
    event = PlanningEvent.objects.get()
    assert event.recipient == member
    assert event.destination["workspace"] == "student"
    assert event.destination["target_id"] == first.data["resource"]["id"]
    assert not PlanningEvent.objects.filter(recipient=owner).exists()
    assert (
        not {"requirements", "rules", "note", "email", "participant_ids"}
        & event.destination.keys()
    )
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            create(rental_participants, group)
            raise RuntimeError("rollback")
    assert AcademicHousingPlan.objects.count() == PlanningEvent.objects.count() == 1


def test_old_event_opens_current_plan_and_private_requirements_stay_private(
    rental_participants, group
):
    owner, tenant, member, _, _ = rental_participants
    plan = create(rental_participants, group)
    old = PlanningEvent.objects.get()
    current = fixtures.requirements(tenant, plan, internet="Private requirement marker")
    assert current["revision"] > old.destination["resource_revision"]
    assert authorize(member, old.destination)
    assert "Private requirement marker" not in str(
        list(PlanningEvent.objects.values_list("destination", flat=True))
    )
    read = fixtures.read(member, plan["id"])
    assert "Private requirement marker" not in str(read)
    assert read["revision"] == current["revision"]
    assert (
        fixtures.authenticated(owner)
        .get(fixtures.API + f"academic-plans/{plan['id']}/")
        .status_code
        == 404
    )


@pytest.mark.parametrize("when", ["before_queue", "after_failed_push", "rejoined"])
def test_membership_is_rechecked_without_replaying_the_command(
    rental_participants, group, when
):
    _, _, member, _, _ = rental_participants
    create(rental_participants, group)
    DeviceToken.objects.create(
        user=member, token="student-event-device", device_type="android"
    )
    if when != "before_queue":
        deliver_planning_events()
        with patch(SEND, return_value=False):
            assert dispatch() == 0
    group.memberships.filter(user=member).update(status="left")
    if when == "rejoined":
        group.memberships.filter(user=member).update(status="active", joined_revision=2)
        AcademicHousingPlan.objects.update(access_group_revision=2)
    with patch(SEND) as send:
        deliver_planning_events()
        PushDelivery.objects.update(
            next_attempt_at=timezone.now() - timedelta(seconds=1)
        )
        assert dispatch() == 0
        send.assert_not_called()
    assert AcademicHousingPlan.objects.count() == 1
    if when == "before_queue":
        assert Notification.objects.count() == 0
        assert PlanningEvent.objects.get().delivery_status == "stale_or_unauthorized"
    else:
        assert PushDelivery.objects.get().suppressed


def test_bridge_and_device_retry_keep_one_receipt_and_business_revision(
    rental_participants, group
):
    _, _, member, _, _ = rental_participants
    plan = create(rental_participants, group)
    DeviceToken.objects.create(
        user=member, token="student-event-device", device_type="android"
    )
    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_user"
    ) as direct:
        deliver_planning_events()
        deliver_planning_events()
        direct.assert_not_called()
    notice = Notification.objects.get()
    assert notice.scope == "student" and PushDelivery.objects.count() == 1
    with patch(SEND, side_effect=[False, True]) as send:
        assert dispatch() == 0
        PushDelivery.objects.update(
            next_attempt_at=timezone.now() - timedelta(seconds=1)
        )
        assert dispatch() == 1
        assert dispatch() == 0
    assert {call.kwargs["data"]["notification_id"] for call in send.call_args_list} == {
        str(notice.id)
    }
    assert AcademicHousingPlan.objects.get().revision == plan["revision"]


def test_arrangement_destination_and_history_use_the_same_resource(
    rental_participants, group
):
    owner, tenant, member, _, _ = rental_participants
    plan = create(rental_participants, group)
    value = fixtures.post(
        tenant,
        f"academic-plans/{plan['id']}/arrangements/",
        command(
            plan_revision=plan["revision"],
            kind="exam",
            starts_on=plan["starts_on"],
            ends_on_exclusive=plan["ends_on_exclusive"],
            rules={"quiet_hours": "22:00–07:00"},
        ),
        201,
    ).data["resource"]
    event = PlanningEvent.objects.get(
        destination__event_kind="student_arrangement_changed"
    )
    assert event.destination["target_id"] == value["id"]
    assert event.destination["academic_plan_id"] == plan["id"]
    assert authorize(member, event.destination)
    with pytest.raises((NotFound, Http404)):
        authorize(member, {**event.destination, "target_id": plan["id"]})
    fixtures.post(
        member,
        f"student-arrangements/{value['id']}/decide/",
        command(
            value["revision"],
            consent=True,
            digest=value["digest"],
        ),
    )
    detail = (
        fixtures.authenticated(member)
        .get(fixtures.API + f"student-arrangements/{value['id']}/")
        .data
    )
    assert detail["id"] == value["id"] and detail["plan"]["id"] == plan["id"]
    history = fixtures.authenticated(member).get(
        fixtures.API + f"student-arrangements/{value['id']}/history/"
    )
    assert history.status_code == 200, history.data
    assert [x["action"] for x in history.data["results"]] == ["accept", "proposed"]
    assert all(
        set(x)
        == {
            "revision",
            "terms_revision",
            "action",
            "created_at",
            "content_available",
            "rules",
            "starts_on",
            "ends_on_exclusive",
        }
        for x in history.data["results"]
    )
    assert history.data["results"][-1]["rules"]["quiet_hours"] == "22:00–07:00"
    group.memberships.filter(user=member).update(joined_revision=2)
    AcademicHousingPlan.objects.filter(id=plan["id"]).update(access_group_revision=2)
    later = fixtures.authenticated(member).get(
        fixtures.API + f"student-arrangements/{value['id']}/history/"
    )
    assert later.status_code == 200
    assert all(
        not row["content_available"] and "rules" not in row
        for row in later.data["results"]
    )
    assert (
        fixtures.authenticated(owner)
        .get(fixtures.API + f"student-arrangements/{value['id']}/history/")
        .status_code
        == 404
    )
    assert not Lease.objects.exists()


def test_nonresident_coordinator_gets_no_arrangement_creation_action(
    rental_participants, group
):
    _, tenant, member, prop, _ = rental_participants
    value = fixtures.create_plan(tenant, prop, group=group, people=[member])
    plan = AcademicHousingPlan.objects.get(id=value["id"])
    assert "propose_arrangement" not in value["allowed_actions"]
    assert actions(tenant, "exam_arrangements", plan.id) == ["read"]
    assert "propose" in actions(member, "exam_arrangements", plan.id)
    value = fixtures.read(member, plan.id)
    assert "propose_arrangement" in value["allowed_actions"]


def test_removed_resident_gets_removal_notice_but_no_future_updates(
    rental_participants, group
):
    _, tenant, member, prop, _ = rental_participants
    value = create(rental_participants, group)
    old = PlanningEvent.objects.get()
    body = fixtures.plan_body(tenant, prop, group=group, people=[tenant])
    body["expected_revision"] = value["revision"]
    edited = fixtures.post(tenant, f"academic-plans/{value['id']}/edit/", body).data[
        "resource"
    ]
    notice = PlanningEvent.objects.exclude(pk=old.pk).get()
    assert notice.destination["recipient_removed"] is True
    assert authorize(member, notice.destination)
    with pytest.raises(NotFound):
        authorize(member, old.destination)
    fixtures.requirements(tenant, edited)
    assert PlanningEvent.objects.filter(recipient=member).count() == 2


@pytest.mark.django_db(transaction=True)
def test_two_workers_queue_only_one_inbox_receipt(rental_participants, group):
    _, _, member, _, _ = rental_participants
    create(rental_participants, group)
    DeviceToken.objects.create(
        user=member, token="student-worker-device", device_type="android"
    )
    barrier = Barrier(2)

    def worker():
        connections.close_all()
        try:
            barrier.wait(timeout=5)
            return deliver_planning_events(event_kinds=["student_plan_changed"])
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        values = list(pool.map(lambda _: worker(), range(2)))
    assert sum(values) == 1
    assert Notification.objects.count() == PushDelivery.objects.count() == 1
