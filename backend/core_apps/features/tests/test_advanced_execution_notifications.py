"""Execution notices preserve step identity and each participant's read scope."""

# flake8: noqa: F401,F811
import pytest
from django.db import transaction
from unittest.mock import patch
from rest_framework.exceptions import NotFound
from core_apps.features.advanced_execution_models import AdvancedExecution
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.advanced_execution.plans import record_step
from core_apps.features.services.advanced_execution.notifications import (
    record,
    EVENT_KIND,
)
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.features.services.planning_notifications_parts.event_copy import (
    event_copy,
)
from .test_advanced_execution import (
    scenario,
    rental_participants,
    execution_enabled,
    ready,
)

pytestmark = pytest.mark.django_db


def prepared(scenario, **kwargs):
    return AdvancedExecution.objects.get(id=ready(scenario, **kwargs)["id"])


def test_plan_notice_is_private_durable_and_idempotent(scenario):
    plan = prepared(scenario, prepare=False)
    step = plan.steps.get(kind="plan_created")
    event = PlanningEvent.objects.get(event_key=f"advanced.execution:{step.id}")
    assert event.recipient == scenario[0]
    assert event.destination["workspace"] == "owner"
    assert event.destination["target_id"] == str(plan.id)
    assert event.destination["execution_step_id"] == str(step.id)
    assert "terms" not in event.destination and "amount" not in event.destination
    record(step)
    assert PlanningEvent.objects.filter(event_key=event.event_key).count() == 1
    deliver_planning_events(event_kinds=[EVENT_KIND])
    event.refresh_from_db()
    original = event.notification_id
    assert original and event.notification.scope == "owner"
    deliver_planning_events(event_kinds=[EVENT_KIND])
    event.refresh_from_db()
    assert event.notification_id == original


def test_leg_notice_does_not_disclose_other_participant_progress(scenario):
    plan = prepared(scenario, two=True, prepare=False)
    own = str(scenario[1].id)
    leg = next(row for row in plan.legs.all() if own in row.actor_ids)
    step = record_step(plan, leg, "canonical_progress", "signed", actor=scenario[0])
    events = PlanningEvent.objects.filter(event_key=f"advanced.execution:{step.id}")
    assert not events.filter(recipient=scenario[2]).exists()
    event = events.get(recipient=scenario[1])
    plan.revision += 1
    plan.save(update_fields=["revision"])
    assert event_copy(event)["title"]  # An older notice still opens current history.
    event.recipient = scenario[2]
    with pytest.raises(NotFound):
        event_copy(event)


def test_step_and_notice_rollback_together(scenario):
    plan = prepared(scenario, prepare=False)
    before = PlanningEvent.objects.count()
    with pytest.raises(RuntimeError), transaction.atomic():
        record_step(plan, None, "local_rollback_check", "failed")
        raise RuntimeError("Rollback the command")
    assert PlanningEvent.objects.count() == before
    assert not plan.steps.filter(kind="local_rollback_check").exists()


def test_unknown_result_notifies_without_repeating_unchanged_progress(scenario):
    from core_apps.features.services.advanced_execution.progress import refresh

    plan = prepared(scenario, prepare=False)
    with patch(
        "core_apps.features.services.advanced_execution.progress.outcome",
        side_effect=lambda leg, lease: (leg.state, True),
    ):
        with transaction.atomic():
            refresh(plan, persist=True)
            plan.save()
        step = plan.steps.get(kind="canonical_progress_summary")
        assert step.state == "unknown"
        count = PlanningEvent.objects.count()
        with transaction.atomic():
            refresh(plan, persist=True)
        assert PlanningEvent.objects.count() == count


def test_delivery_rechecks_current_membership_before_any_obligation(scenario):
    plan = prepared(scenario, two=True, prepare=False)
    step = record_step(plan, None, "reviews_changed", "ready", actor=scenario[0])
    event = PlanningEvent.objects.get(
        event_key=f"advanced.execution:{step.id}", recipient=scenario[2]
    )
    from core_apps.features.advanced_tender_models import PackageCandidate

    package = PackageCandidate.objects.get(id=plan.source_id)
    package.tender.group.memberships.filter(user=scenario[2]).update(status="left")
    with pytest.raises(NotFound):
        event_copy(event)
    deliver_planning_events(event_kinds=[EVENT_KIND])
    event.refresh_from_db()
    assert event.delivery_status == "stale_or_unauthorized"
    assert not event.notification_id
