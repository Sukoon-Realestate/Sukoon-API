"""Participants rediscover their own original cases without reissuing commands."""

import uuid

import pytest
from rest_framework.exceptions import NotFound

from core_apps.features.models import (
    IdempotencyRecord,
    RentalOperationalCase,
    ReviewReport,
    ReviewSection,
)
from core_apps.features.services.reputation import moderation
from core_apps.features.services.reputation.tasks import authorize_notification
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.tests.test_reputation import (
    actors,
    approve,
    client,
    send_pair,
)

BASE = "/api/v1/features/v1/reviews/cases/"


@pytest.fixture
def original_cases(actors):
    case, _, _, _, receipt = send_pair(actors)
    section = ReviewSection.objects.get(id=receipt["section_ids"][0])
    approve(actors, section)
    section.refresh_from_db()
    report = moderation.section_action(
        actors[1],
        section.id,
        "reports",
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": section.revision,
            "reason_code": "outside_experience",
            "detail": "Private participant report",
        },
    )
    held = moderation.moderate(
        actors[4],
        section.id,
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": section.revision,
            "action": "hold",
            "reason": "Independent content inspection",
        },
    )
    decision = section.decisions.get(action="hold")
    appeal = moderation.appeal_decision(
        actors[1],
        decision.id,
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": held["revision"],
            "detail": "Private original appeal",
        },
    )
    response = client(actors[1]).post(
        "/api/v1/features/v1/reviews/eligibility-requests/",
        {
            "request_key": str(uuid.uuid4()),
            "source_kind": "tenancy",
            "source_id": str(case.lease.id),
            "detail": "Private source investigation",
        },
        format="json",
    )
    assert response.status_code == 200
    return actors, {report["id"], appeal["id"], response.data["id"]}, report["id"]


def test_original_cases_are_paginated_and_rediscoverable_without_reissue(
    original_cases,
):
    people, identities, _ = original_cases
    api = client(people[1])
    before = IdempotencyRecord.objects.count()
    first = api.get(BASE, {"page_size": 2})
    assert first.status_code == 200
    assert first.data["count"] == 3 and first.data["total_pages"] == 2
    second = api.get(BASE, {"page_size": 2, "page": 2})
    rows = first.data["results"] + second.data["results"]
    assert {row["id"] for row in rows} == identities
    assert {row["kind"] for row in rows} == {"report", "appeal", "eligibility"}
    for row in rows:
        assert set(row) == {"id", "kind", "state", "revision", "created_at"}
        detail = api.get(BASE + row["id"] + "/")
        assert detail.status_code == 200 and detail.data["id"] == row["id"]
    assert IdempotencyRecord.objects.count() == before
    assert "private" in first["Cache-Control"] and "no-store" in first["Cache-Control"]


@pytest.mark.parametrize("actor_index", [0, 2, 3, 4, 5])
def test_other_participants_and_operators_cannot_reuse_personal_case_discovery(
    original_cases,
    actor_index,
):
    people, identities, _ = original_cases
    api = client(people[actor_index])
    response = api.get(BASE, {"reporter_id": str(people[1].id), "page_size": 1000})
    assert response.status_code == 200
    assert response.data["results"] == [] and response.data["per_page"] == 100
    for identifier in identities:
        assert api.get(BASE + identifier + "/").status_code == 404


def test_resolved_case_remains_discoverable_with_its_canonical_explanation(
    original_cases, settings
):
    people, identities, report_id = original_cases
    report = ReviewReport.objects.get(id=report_id)
    moderation.resolve_report(
        people[4],
        report.id,
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": report.revision,
            "reason": "Original context inspected; no removal required.",
        },
    )
    settings.REVIEWS_ENABLED = False
    api = client(people[1])
    result = api.get(BASE)
    assert result.status_code == 200
    assert {row["id"] for row in result.data["results"]} == identities
    row = next(row for row in result.data["results"] if row["id"] == report_id)
    assert row["state"] == "resolved"
    detail = api.get(BASE + report_id + "/")
    assert (
        detail.data["resolution"] == "Original context inspected; no removal required."
    )


def test_unrelated_operational_cases_are_not_exposed_as_review_cases(original_cases):
    people, identities, _ = original_cases
    original = RentalOperationalCase.objects.get(kind="review_eligibility")
    RentalOperationalCase.objects.create(
        source_key="unrelated-private-case",
        kind="payment_unknown",
        opened_by=people[1],
        due_at=original.due_at,
        reason="Unrelated financial evidence",
        next_action="Review",
    )
    response = client(people[1]).get(BASE)
    assert response.status_code == 200
    assert {row["id"] for row in response.data["results"]} == identities


def test_anonymous_case_discovery_is_rejected(actors):
    assert client().get(BASE).status_code == 401


def test_empty_history_is_not_a_failed_request(actors):
    response = client(actors[1]).get(BASE)
    assert response.status_code == 200
    assert response.data["count"] == 0 and response.data["results"] == []


def resolved_event(original_cases):
    people, _, report_id = original_cases
    report = ReviewReport.objects.get(id=report_id)
    body = {
        "request_key": str(uuid.uuid4()),
        "expected_revision": report.revision,
        "reason": "Original report independently resolved",
    }
    moderation.resolve_report(people[4], report.id, body)
    moderation.resolve_report(people[4], report.id, body)
    event = PlanningEvent.objects.get(destination__review_case_id=report_id)
    assert event.recipient_id == people[1].pk
    assert event.destination["target_id"] == str(report.section.id)
    assert event.destination["action_type"] == "open_review_section"
    return event


def test_case_result_notification_reuses_original_identity_after_source_withdrawal(
    original_cases,
):
    event = resolved_event(original_cases)
    report = ReviewReport.objects.get(id=event.destination["review_case_id"])
    report.section.content_state = "withdrawn"
    report.section.save(update_fields=["content_state"])
    authorize_notification(event)
    assert set(event.destination) == {
        "action_type",
        "target_id",
        "review_event",
        "review_case_id",
    }
    assert "resolution" not in event.destination and "comment" not in event.destination


@pytest.mark.parametrize(
    "change", ["recipient", "invalid_id", "wrong_source", "wrong_kind"]
)
def test_case_notification_rechecks_exact_private_owner_and_source(
    original_cases, change
):
    event = resolved_event(original_cases)
    if change == "recipient":
        event.recipient = original_cases[0][4]
    elif change == "invalid_id":
        event.destination["review_case_id"] = "not-a-case"
    elif change == "wrong_source":
        event.destination["target_id"] = str(uuid.uuid4())
    else:
        event.destination["review_event"] = "review_appeal_resolved"
    with pytest.raises(NotFound):
        authorize_notification(event)


def test_actual_case_delivery_is_durable_and_repeated_scan_does_not_duplicate(
    original_cases, monkeypatch
):
    from core_apps.features.services.planning_notifications import (
        deliver_planning_events,
    )
    from core_apps.notifications.services.fcm_service import FCMService

    event = resolved_event(original_cases)
    # The external push transport is replaced. Inbox creation and the worker's
    # authorization, event identity and persistence are the real implementation.
    monkeypatch.setattr(FCMService, "send_push_to_user", lambda **kwargs: 1)
    deliver_planning_events()
    event.refresh_from_db()
    assert event.notification_id and event.delivered_at
    original_notification = event.notification_id
    assert (
        event.notification.data["review_case_id"] == event.destination["review_case_id"]
    )
    deliver_planning_events()
    event.refresh_from_db()
    assert event.notification_id == original_notification and event.attempts == 1
