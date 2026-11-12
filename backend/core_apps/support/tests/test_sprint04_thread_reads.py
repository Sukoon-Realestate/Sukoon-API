"""Legacy projection oracles and independently bounded support relations."""

from copy import deepcopy
from unittest.mock import patch

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.exceptions import ValidationError

from core_apps.support.models import (
    Ticket, TicketMessage, TicketAttachment, TicketInformationRequest,
    TicketInformationEvent, TicketEvidenceSubmission, TicketInternalNote,
    TicketTransition,
)
from core_apps.support.serializers.ticket import TicketDetailSerializer
from core_apps.support.services.information import projection
from core_apps.support.services.operations import projection as staff_projection
from core_apps.support.services.read_pages import ReadPages
from core_apps.support.services.ticket_service import get_ticket_detail
from tools.qa.performance import measured

pytestmark = pytest.mark.django_db


def populated(user, size=8, depth=7):
    ticket = Ticket.objects.create(
        user=user, workspace="tenant", category="other", subject="Synthetic thread")
    for i in range(size):
        message = TicketMessage.objects.create(
            ticket=ticket, sender_user=user, body=f"Synthetic message {i}")
        for j in range(depth):
            TicketAttachment.objects.create(
                message=message, name=f"Synthetic file {j}", status="attached",
                private_file="synthetic/not-read", private_content=b"unread",
                content_sha256="digest")
        row = TicketInformationRequest.objects.create(
            ticket=ticket, source_message=message, answer=message,
            created_by=user, prompt=f"Synthetic prompt {i}")
        for j in range(depth):
            TicketInformationEvent.objects.create(
                request=row, actor=user, action="answer_sent", revision=j + 1,
                answer=message)
            evidence_message = TicketMessage.objects.create(
                ticket=ticket, sender_user=user, body="Synthetic evidence")
            TicketEvidenceSubmission.objects.create(
                request=row, message=evidence_message, version=j + 1,
                files=[{"id": str(message.attachments.first().id), "sha256": "digest"}])
        TicketInternalNote.objects.create(ticket=ticket, actor=user, body="Private staff note")
        TicketTransition.objects.create(ticket=ticket, actor=user, revision=i + 1,
                                        action="note", reason="Synthetic")
    return ticket


def detail(user, ticket, params=None):
    return TicketDetailSerializer(get_ticket_detail(
        user, str(ticket.id), "tenant", read_params=params)).data


@pytest.mark.parametrize("size", [1, 10, 100])
def test_legacy_staff_messages_batch_attachments(size, user, another_user):
    ticket = populated(user, size=size, depth=1)
    ticket = Ticket.objects.select_related("user", "assigned_to").get(pk=ticket.pk)
    value, report = measured("support-staff-thread", size, lambda: staff_projection(
        ticket, another_user, detail=True))
    assert len(value["messages"]) == size * 2
    assert len(value["internal_notes"]) == size
    assert len(value["information_requests"]) == size
    assert "pages" not in value
    assert report["queries"] <= 12


def test_consumer_pages_match_legacy_without_staff_data(user):
    ticket = populated(user)
    legacy = detail(user, ticket)
    params = {"bounded": "true", "messages_page": "2", "messages_page_size": "3",
              "information_requests_page": "2", "information_requests_page_size": "3",
              "history_page": "2", "history_page_size": "2",
              "evidence_versions_page": "2", "evidence_versions_page_size": "2",
              "attachments_page_size": "2"}
    value = detail(user, ticket, params)
    for actual, original in zip(value["messages"], legacy["messages"][3:6]):
        expected = deepcopy(original)
        expected["attachments"] = expected["attachments"][:2]
        assert {k: v for k, v in actual.items() if k != "pages"} == expected
        assert actual["pages"]["attachments"]["count"] == len(original["attachments"])
    for actual, expected in zip(value["information_requests"], legacy["information_requests"][3:6]):
        expected = deepcopy(expected)
        expected["history"] = expected["history"][2:4]
        expected["evidence_versions"] = expected["evidence_versions"][2:4]
        assert {k: v for k, v in actual.items() if k != "pages"} == expected
        assert actual["pages"]["history"]["count"] == 7
    assert value["pages"]["messages"]["count"] == 64
    assert value["pages"]["information_requests"]["count"] == 8
    assert "internal_notes" not in value and "transitions" not in value
    assert "pages" not in legacy
    assert detail(user, ticket, {"bounded": "false"}) == legacy


@pytest.mark.parametrize("size", [1, 10, 100])
def test_bounded_nested_projection_cost_and_current_proof(size, user, another_user):
    ticket = populated(user, size=size, depth=6)
    ticket = Ticket.objects.select_related("user", "assigned_to").get(pk=ticket.pk)
    params = {"bounded": "true", **{f"{name}_page_size": "2" for name in ReadPages.limits}}
    value, report = measured("support-bounded-thread", size, lambda: staff_projection(
        ticket, another_user, detail=True, read_params=params))
    assert len(value["messages"]) == 2
    assert len(value["internal_notes"]) == min(size, 2)
    assert len(value["transitions"]) == min(size, 2)
    assert len(value["information_requests"]) == min(size, 2)
    for row in value["information_requests"]:
        assert len(row["history"]) == len(row["evidence_versions"]) == 2
        assert row["pages"]["history"]["count"] == 6
        # A file attached to a different message does not prove this submission.
        assert not row["evidence_versions"][0]["files"][0]["available"]
    assert value["pages"]["messages"]["count"] == size * 7
    assert report["queries"] <= 20
    assert report["payload_bytes"] < 16000


def test_current_evidence_and_revocation_on_selected_page(user):
    ticket = populated(user, size=1, depth=3)
    submission = ticket.information_requests.first().evidence_versions.get(version=2)
    file = TicketAttachment.objects.get(id=submission.files[0]["id"])
    TicketAttachment.objects.filter(pk=file.pk).update(message=submission.message)
    ticket.read_bounds = ReadPages({"evidence_versions_page": "2", "evidence_versions_page_size": "1"})
    assert projection(ticket)[0]["evidence_versions"][0]["files"][0]["available"]
    TicketAttachment.objects.filter(pk=file.pk).update(status="revoked")
    assert not projection(ticket)[0]["evidence_versions"][0]["files"][0]["available"]


@pytest.mark.parametrize("params", [
    {"bounded": "maybe"}, {"bounded": "true", "history_page_size": "21"},
    {"bounded": "true", "messages_page_size": "101"},
    {"bounded": "true", "messages_page": "0"},
    {"bounded": "true", "messages_page": "10001"},
    {"bounded": "true", "history_page": "-1"},
    {"bounded": "true", "history_page": "١"},
])
def test_invalid_controls_validated_after_ownership_and_workspace(params, user, another_user):
    ticket = populated(user, size=1, depth=1)
    with patch("core_apps.support.services.read_pages.prepare_messages") as prepare:
        with pytest.raises(Ticket.DoesNotExist):
            get_ticket_detail(another_user, str(ticket.id), read_params=params)
        with pytest.raises(Ticket.DoesNotExist):
            get_ticket_detail(user, str(ticket.id), "owner", read_params=params)
        prepare.assert_not_called()
        with pytest.raises(ValidationError):
            get_ticket_detail(user, str(ticket.id), read_params=params)
        prepare.assert_not_called()


def test_http_opt_in_and_ownership_before_history_queries(auth_client, user, another_user):
    ticket = populated(user, size=1, depth=1)
    url = reverse("support-ticket-detail", kwargs={"id": ticket.id})
    response = auth_client.get(url, {"bounded": "true", "messages_page_size": 1})
    assert response.status_code == 200
    assert b'"page_size":1' in response.content
    auth_client.force_authenticate(another_user)
    with CaptureQueriesContext(connection) as queries:
        response = auth_client.get(url, {"bounded": "true", "history_page": "bad"})
    assert response.status_code == 404
    assert not any('support_ticketmessage' in query["sql"].lower() for query in queries)


def test_empty_pages_and_private_bytes_not_loaded(user):
    ticket = populated(user, size=1, depth=1)
    with CaptureQueriesContext(connection) as queries:
        value = detail(user, ticket, {"bounded": "true", "messages_page": "999"})
    assert value["messages"] == []
    assert value["pages"]["messages"]["count"] == 2
    assert not value["pages"]["messages"]["has_next"]
    assert all('"private_content"' not in query["sql"] for query in queries)


def test_staff_http_pages_and_revoked_role(auth_client, user):
    from core_apps.support.tests.test_shared_admin import operator

    ticket = populated(user, size=3, depth=2)
    agent = operator("bounded-support")
    auth_client.force_authenticate(agent)
    url = reverse("admin-support-detail", args=[ticket.id])
    response = auth_client.get(url, {
        "bounded": "true", "internal_notes_page": 2, "internal_notes_page_size": 1,
    })
    assert response.status_code == 200
    assert len(response.data["internal_notes"]) == 1
    assert response.data["pages"]["internal_notes"] == {
        "count": 3, "page": 2, "page_size": 1, "has_next": True}
    assert auth_client.get(url).data.get("pages") is None
    agent.staff_profile.is_active = False
    agent.staff_profile.save(update_fields=["is_active"])
    with patch("core_apps.support.services.read_pages.ReadPages.parse") as parse:
        response = auth_client.get(url, {"bounded": "bad"})
    assert response.status_code == 403
    parse.assert_not_called()


def test_reply_retains_full_legacy_receipt_with_bounded_query(auth_client, user):
    from uuid import uuid4

    ticket = populated(user, size=2, depth=1)
    url = reverse("support-ticket-reply", kwargs={"id": ticket.id})
    response = auth_client.post(
        url + "?bounded=true&messages_page_size=bad", {"body": "Synthetic reply"},
        format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()))
    assert response.status_code == 200
    assert b'"Synthetic reply"' in response.content
    assert b'"pages"' not in response.content
    assert ticket.messages.count() == 5


def test_equal_timestamps_page_without_gaps_and_nested_pages_are_per_parent(user):
    from django.utils import timezone

    ticket = populated(user, size=4, depth=3)
    stamp = timezone.now()
    ticket.messages.update(created_at=stamp)
    ticket.information_requests.update(created_at=stamp)
    TicketInformationEvent.objects.filter(request__ticket=ticket).update(created_at=stamp)
    legacy = detail(user, ticket)
    seen = []
    for number in range(1, 9):
        value = detail(user, ticket, {
            "bounded": "true", "messages_page": str(number), "messages_page_size": "2",
            "information_requests_page_size": "4", "history_page": "2",
            "history_page_size": "1", "evidence_versions_page_size": "1",
        })
        seen.extend(row["id"] for row in value["messages"])
        for actual, original in zip(value["information_requests"], legacy["information_requests"]):
            assert actual["history"] == original["history"][1:2]
            assert len(actual["evidence_versions"]) == 1
    assert seen == [row["id"] for row in legacy["messages"]]
    assert len(seen) == len(set(seen))
