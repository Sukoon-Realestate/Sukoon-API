"""Explicit event selection uses the ordinary authorized planning outbox bridge."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.db import connections, transaction
from django.utils import timezone

from core_apps.features.company_models import (
    Company,
    CompanyHousingRequest,
    CompanyMembership,
)
from core_apps.features.models import SearchAlert
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.company import role_notifications, tenancy_access
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.notifications.models import DeviceToken, Notification, PushDelivery
from .test_company_tenancy import (  # noqa: F401
    agreement,
    cycle,
    company_setup,
    rental_participants,
    policy,
)

pytestmark = pytest.mark.django_db
SEND = "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device"


@pytest.fixture
def events():
    result = []
    for label in ("selected", "unrelated"):
        user = get_user_model().objects.create_user(
            email=f"targeted-{label}@example.test", password="local"
        )
        alert = SearchAlert.objects.create(user=user, name=label, cadence="daily")
        DeviceToken.objects.create(user=user, token=f"local-targeted-{label}")
        result.append(
            PlanningEvent.objects.create(
                recipient=user,
                event_key=f"search-alert:targeted:{label}",
                destination={
                    "action_type": "open_search_alert",
                    "event_kind": "search_alert_updated",
                    "target_id": str(alert.id),
                    "workspace": "student",
                    "revision": alert.revision,
                },
            )
        )
    return result


def state(query=None):
    query = PlanningEvent.objects.all() if query is None else query
    return list(query.order_by("id").values())


@pytest.fixture
def company_event(agreement):
    actors, item, _, _ = agreement
    with transaction.atomic():
        tenancy_access.changed(item, actors["owner"], "company_signature_requested")
    event = PlanningEvent.objects.get(
        recipient=actors["signer"],
        event_key=f"company.tenancy:{item.id}:{item.revision}:signer",
    )
    DeviceToken.objects.create(user=actors["signer"], token="local-targeted-signer")
    # An independent, valid company destination must remain pending too.
    other = get_user_model().objects.create_user(
        email="targeted-other-company@example.test", password="local", is_verified=True
    )
    company = Company.objects.create(
        name="Other synthetic company",
        registration_number="TARGETED-OTHER",
        contact_email="targeted-other-company@example.test",
    )
    CompanyMembership.objects.create(company=company, user=other, is_admin=True)
    request = CompanyHousingRequest.objects.create(
        company=company,
        requester=other,
        coordinator=other,
        title="Other synthetic need",
        purpose="Isolated notification delivery verification",
        location="Synthetic Cairo",
        starts_on=timezone.localdate(),
        ends_on_exclusive=timezone.localdate() + timedelta(days=31),
        headcount=1,
        commitment_ceiling_minor=10000,
        deposit_limit_minor=10000,
    )
    role_notifications.record(
        user=other,
        company=company,
        role="admin",
        key=f"company.request:{request.id}:1",
        destination={
            "action_type": "open_company_request",
            "target_id": str(request.id),
            "workspace": "company",
            "revision": request.revision,
        },
    )
    return actors, item, event, company


def test_exact_company_event_only_and_replay_reuses_notice_and_push(company_event):
    actors, item, event, other_company = company_event
    others = PlanningEvent.objects.exclude(id=event.id)
    before = state(others)
    assert others.filter(destination__company_id=str(other_company.id)).exists()
    assert (
        others.filter(destination__company_id=str(actors["company"].id))
        .exclude(recipient=actors["signer"])
        .exists()
    )
    notice_count, push_count = (
        Notification.objects.count(),
        PushDelivery.objects.count(),
    )
    with patch(SEND) as send:
        assert deliver_planning_events(event_ids=[str(event.id)]) == 1
        event.refresh_from_db()
        notice_id = event.notification_id
        assert deliver_planning_events(event_ids=[event.id, event.id]) == 0
        send.assert_not_called()
    event.refresh_from_db()
    assert event.notification_id == notice_id and event.attempts == 1
    assert event.delivered_at and event.delivery_status == "push_queued"
    assert event.provider_accepted_at is None
    notice = event.notification
    assert notice.scope == "company" and not notice.is_read
    assert notice.user_id == actors["signer"].pk
    assert notice.data["event_id"] == str(event.id)
    assert notice.data["event_source"] == "planning"
    assert notice.data["company_id"] == str(actors["company"].id)
    assert notice.data["company_role"] == "signer"
    assert notice.data["target_id"] == str(item.id)
    assert notice.data["lease_id"] == str(item.lease.id)
    assert Notification.objects.count() == notice_count + 1
    assert PushDelivery.objects.count() == push_count + 1
    delivery = PushDelivery.objects.get(notification=notice)
    assert delivery.attempts == 0 and delivery.accepted_at is None
    assert state(others) == before


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        [],
        (),
        "",
        str(uuid.uuid4()),
        uuid.uuid4(),
        {},
        {uuid.uuid4()},
        iter([uuid.uuid4()]),
        [None],
        [123],
        [b"invalid"],
        ["not-a-uuid"],
        [uuid.uuid4(), "not-a-uuid"],
        [uuid.uuid4() for _ in range(101)],
    ],
    ids=[
        "none",
        "empty-list",
        "empty-tuple",
        "empty-string",
        "bare-string",
        "bare-uuid",
        "dict",
        "set",
        "iterator",
        "null-entry",
        "integer-entry",
        "bytes-entry",
        "malformed",
        "partially-valid",
        "over-limit",
    ],
)
def test_invalid_explicit_selection_fails_before_any_query(
    events, invalid, django_db_blocker
):
    before = state()
    with django_db_blocker.block(), pytest.raises(ValueError, match="event_ids"):
        deliver_planning_events(event_ids=invalid)
    assert state() == before
    assert not Notification.objects.exists() and not PushDelivery.objects.exists()


def test_unknown_ids_and_kind_intersection_never_expand_selection(events):
    selected, _ = events
    before = state()
    # The accepted upper bound still cannot fall back to processing all events.
    assert deliver_planning_events(event_ids=[uuid.uuid4() for _ in range(100)]) == 0
    assert (
        deliver_planning_events(
            event_ids=[selected.id], event_kinds=["company_tenancy_updated"]
        )
        == 0
    )
    assert state() == before
    assert (
        deliver_planning_events(
            event_ids=(str(selected.id),), event_kinds=["search_alert_updated"]
        )
        == 1
    )
    assert state(PlanningEvent.objects.exclude(id=selected.id)) == [
        before_row for before_row in before if before_row["id"] != selected.id
    ]


def test_omitted_selection_preserves_general_worker_and_integer_result(events):
    with patch(SEND) as send:
        assert deliver_planning_events() == 2
        assert deliver_planning_events() == 0
        send.assert_not_called()
    assert Notification.objects.count() == PushDelivery.objects.count() == 2


@pytest.mark.parametrize("blocked", ["retry-delay", "exhausted", "inactive"])
def test_selected_event_keeps_due_attempt_and_active_recipient_guards(events, blocked):
    selected, _ = events
    if blocked == "inactive":
        selected.recipient.is_active = False
        selected.recipient.save(update_fields=["is_active"])
    else:
        selected.attempts = 5 if blocked == "exhausted" else 1
        selected.save(update_fields=["attempts", "updated_at"])
        if blocked == "exhausted":
            PlanningEvent.objects.filter(id=selected.id).update(
                updated_at=timezone.now() - timedelta(minutes=3)
            )
    before = state()
    assert deliver_planning_events(event_ids=[selected.id]) == 0
    assert state() == before
    assert not Notification.objects.exists() and not PushDelivery.objects.exists()


def test_due_selected_retry_uses_normal_bridge_without_touching_other_event(events):
    selected, other = events
    PlanningEvent.objects.filter(id=selected.id).update(
        attempts=1, updated_at=timezone.now() - timedelta(minutes=3)
    )
    before = state(PlanningEvent.objects.filter(id=other.id))
    assert deliver_planning_events(event_ids=[selected.id]) == 1
    selected.refresh_from_db()
    assert selected.attempts == 2 and selected.delivery_status == "push_queued"
    assert state(PlanningEvent.objects.filter(id=other.id)) == before


@pytest.mark.parametrize("revoked", ["membership", "mandate"])
def test_stale_company_authority_is_handled_without_notice_or_unrelated_changes(
    company_event, revoked
):
    actors, item, event, _ = company_event
    if revoked == "membership":
        CompanyMembership.objects.filter(
            company=actors["company"], user=actors["signer"]
        ).update(is_active=False)
    else:
        item.signer_mandate.state = "revoked"
        item.signer_mandate.save(update_fields=["state"])
    others = PlanningEvent.objects.exclude(id=event.id)
    before = state(others)
    counts = (Notification.objects.count(), PushDelivery.objects.count())
    with patch(SEND) as send:
        assert deliver_planning_events(event_ids=[event.id]) == 0
        assert deliver_planning_events(event_ids=[event.id]) == 0
        send.assert_not_called()
    event.refresh_from_db()
    assert event.delivered_at and event.delivery_status == "stale_or_unauthorized"
    assert event.attempts == 0 and event.notification_id is None
    assert (Notification.objects.count(), PushDelivery.objects.count()) == counts
    assert state(others) == before


def test_queue_failure_rolls_back_only_selected_event_and_can_recover(events):
    selected, other = events
    before = state()
    with patch(
        "core_apps.notifications.services.push_delivery.queue_notification",
        side_effect=RuntimeError("synthetic queue failure"),
    ), pytest.raises(RuntimeError, match="synthetic queue failure"):
        deliver_planning_events(event_ids=[selected.id])
    assert state() == before
    assert not Notification.objects.exists() and not PushDelivery.objects.exists()
    assert deliver_planning_events(event_ids=[selected.id]) == 1
    other.refresh_from_db()
    assert other.delivered_at is None and other.notification_id is None
    assert Notification.objects.count() == PushDelivery.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_targeted_workers_keep_one_notice_and_push(events):
    selected, other = events

    def run(_):
        connections.close_all()
        try:
            return deliver_planning_events(event_ids=[selected.id])
        finally:
            connections.close_all()

    with patch(SEND) as send, ThreadPoolExecutor(max_workers=2) as workers:
        assert sum(workers.map(run, range(2))) == 1
        send.assert_not_called()
    selected.refresh_from_db()
    other.refresh_from_db()
    assert selected.attempts == 1 and selected.delivered_at
    assert other.notification_id is None and other.delivered_at is None
    assert Notification.objects.count() == PushDelivery.objects.count() == 1
