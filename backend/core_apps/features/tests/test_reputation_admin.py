"""Actual admin requests preserve canonical moderation and private evidence."""

import uuid

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse

from core_apps.features.models import (
    ReviewAppeal,
    ReviewAuditEvent,
    ReviewReport,
    ReviewSection,
)
from core_apps.features.services.reputation import (
    generation,
    moderation,
    submission,
    visibility,
)
from core_apps.features.tests.test_reputation import (
    actors,
    approve,
    body,
    client as api_client,
    send_pair,
    stay,
)


@pytest.fixture
def web(actors, settings):
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    browser = Client()
    browser.force_login(actors[4])
    return browser


def location(item):
    return reverse(
        "admin:reputation-" + item._meta.model_name + "-inspect", args=[item.id]
    )


def decision(item, **values):
    return {
        "access_reason": "Inspect the reported source and current content",
        "request_key": str(uuid.uuid4()),
        "expected_revision": item.revision,
        "action": "approve",
        "reason": "Independent content review completed",
        **values,
    }


def section(actors):
    _, _, _, _, result = send_pair(actors)
    return ReviewSection.objects.get(id=result["section_ids"][0])


def test_unreasoned_read_and_generic_change_never_expose_content(actors, web):
    item = section(actors)
    result = web.get(location(item))
    assert result.status_code == 200
    assert item.original_comment not in result.content.decode()
    assert (
        "private" in result["Cache-Control"] and "no-store" in result["Cache-Control"]
    )
    assert result["Referrer-Policy"] == "same-origin"
    assert not ReviewAuditEvent.objects.filter(action="operator_admin_read").exists()
    generic = reverse("admin:features_reviewsection_change", args=[item.pk])
    assert web.post(generic, {"content_state": "approved"}).status_code == 302
    item.refresh_from_db()
    assert item.content_state == "pending"


def test_reasoned_read_is_audited_and_escaped(actors, web):
    item = section(actors)
    item.original_comment = "<script>unsafe()</script>"
    item.save(update_fields=["original_comment"])
    response = web.get(location(item), {"access_reason": "Investigate content"})
    assert response.status_code == 200
    assert "&lt;script&gt;" in response.content.decode()
    assert "<script>unsafe()" not in response.content.decode()
    assert (
        ReviewAuditEvent.objects.filter(
            subject_id=item.id,
            actor=actors[4],
            action="operator_admin_read",
            reason="Investigate content",
        ).count()
        == 1
    )


def test_explicit_moderation_permission_is_sufficient_but_staff_alone_is_not(
    actors, web
):
    item = section(actors)
    operator = actors[3]
    operator.is_staff = True
    operator.save(update_fields=["is_staff"])
    web.force_login(operator)
    assert web.get(location(item)).status_code == 403
    operator.user_permissions.add(Permission.objects.get(codename="moderate_reviews"))
    assert (
        web.get(
            location(item), {"access_reason": "Authorized independent review"}
        ).status_code
        == 200
    )
    assert web.get(reverse("admin:features_reviewsection_add")).status_code == 403
    assert (
        web.get(
            reverse("admin:features_reviewsection_delete", args=[item.pk])
        ).status_code
        == 403
    )


def test_source_party_is_excluded_even_with_superuser_access(actors, web):
    item = section(actors)
    party = actors[0]
    party.is_staff = party.is_superuser = True
    party.save(update_fields=["is_staff", "is_superuser"])
    web.force_login(party)
    response = web.get(reverse("admin:features_reviewsection_changelist"))
    assert response.status_code == 200
    assert str(item.id) not in response.content.decode()
    assert web.get(location(item), {"access_reason": "Own property"}).status_code == 404
    assert web.post(location(item), decision(item)).status_code == 404
    assert not item.decisions.exists()


def test_csrf_and_missing_reason_prevent_commands(actors, web):
    item = section(actors)
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(actors[4])
    assert csrf.post(location(item), decision(item)).status_code == 403
    assert web.post(location(item), decision(item, reason="")).status_code == 200
    assert web.post(location(item), decision(item, access_reason="")).status_code == 200
    assert not item.decisions.exists()


def test_approval_preserves_time_gate_score_and_original_wording(actors, web):
    case = generation.generate_tenancy(stay(actors))
    opportunity = case.opportunities.get(reviewer=actors[1])
    result = submission.submit(actors[1], opportunity.id, body(opportunity))
    item = ReviewSection.objects.get(id=result["section_ids"][0])
    original = item.original_comment
    command = decision(item)
    assert web.post(location(item), command).status_code == 302
    assert web.post(location(item), command).status_code == 302
    item.refresh_from_db()
    case.refresh_from_db()
    assert item.content_state == "approved" and item.revision == 2
    assert item.overall_score == 4 and item.original_comment == original
    assert item.decisions.count() == 1
    assert case.gate_released_at is None and not visibility.published(item)


def test_stale_and_invalid_redaction_leave_original_unchanged(actors, web):
    item = section(actors)
    original = item.original_comment
    assert (
        web.post(location(item), decision(item, expected_revision=500)).status_code
        == 200
    )
    assert (
        web.post(
            location(item),
            decision(
                item, action="redact", redacted_comment="Fabricated replacement opinion"
            ),
        ).status_code
        == 200
    )
    item.refresh_from_db()
    assert (
        item.revision == 1 and item.original_comment == item.public_comment == original
    )
    assert not item.decisions.exists()


def test_report_resolution_reuses_receipt_and_is_visible_only_to_reporter(actors, web):
    item = section(actors)
    approve(actors, item)
    item.refresh_from_db()
    result = moderation.section_action(
        actors[0],
        item.id,
        "reports",
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": item.revision,
            "reason_code": "outside_experience",
            "detail": "Please inspect context",
        },
    )
    report = ReviewReport.objects.get(id=result["id"])
    command = decision(
        report,
        action="resolve",
        reason="Compared with the original experience; no content removal required.",
    )
    assert web.post(location(report), command).status_code == 302
    assert web.post(location(report), command).status_code == 302
    api_result = api_client(actors[4]).post(
        f"/api/v1/admin/review-cases/{report.id}/resolve/",
        {key: command[key] for key in ("request_key", "expected_revision", "reason")},
        format="json",
    )
    assert api_result.status_code == 200
    report.refresh_from_db()
    assert report.state == "resolved" and report.revision == 2
    assert (
        ReviewAuditEvent.objects.filter(
            subject_id=report.id, action="operator_case_resolved"
        ).count()
        == 1
    )
    path = f"/api/v1/features/v1/reviews/cases/{report.id}/"
    response = api_client(actors[0]).get(path)
    assert response.json()["data"]["resolution"] == command["reason"]
    rendered = web.get(
        location(report), {"access_reason": "Inspect historical resolution"}
    )
    assert command["reason"] in rendered.content.decode()
    assert "Record decision</button>" not in rendered.content.decode()
    assert api_client(actors[3]).get(path).status_code == 404
    assert (
        web.post(location(report), decision(report, action="resolve")).status_code
        == 200
    )
    report.refresh_from_db()
    assert report.revision == 2


def test_appeal_requires_second_moderator_and_keeps_original_score(actors, web):
    item = section(actors)
    result = moderation.moderate(
        actors[4],
        item.id,
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": item.revision,
            "action": "hold",
            "reason": "Inspect source context",
        },
    )
    appealed = moderation.appeal_decision(
        actors[1],
        result["id"],
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": 1,
            "detail": "The source supports this opinion",
        },
    )
    appeal = ReviewAppeal.objects.get(id=appealed["id"])
    assert (
        web.get(location(appeal), {"access_reason": "Own decision"}).status_code == 404
    )
    web.force_login(actors[5])
    assert (
        web.post(location(appeal), decision(appeal, action="restore")).status_code
        == 302
    )
    appeal.refresh_from_db()
    item.refresh_from_db()
    assert appeal.state == "resolved" and appeal.resolved_by_id == actors[5].pk
    assert item.content_state == "approved" and item.overall_score == 4
    assert item.decisions.count() == 2


def test_reply_decision_uses_reply_revision_without_mutating_section_score(actors, web):
    item = section(actors)
    approve(actors, item)
    item.refresh_from_db()
    result = moderation.section_action(
        actors[0],
        item.id,
        "reply",
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": item.revision,
            "comment": "Response to this experience",
        },
    )
    assert (
        web.post(
            location(item), decision(item, reply_id=result["id"], expected_revision=1)
        ).status_code
        == 302
    )
    item.refresh_from_db()
    assert item.revision == 2 and item.overall_score == 4
    assert item.reply.content_state == "approved" and item.reply.revision == 2
