"""The advice console can finish an inquiry without closing domain obligations."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.test import Client
from django.urls import reverse
from django.db import close_old_connections, connection
from rest_framework.exceptions import PermissionDenied, ValidationError

from core_apps.features.models import RentalAuditEvent
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.tests.test_rental_lifecycle_safety import operator
from core_apps.support.models import TicketMessage
from core_apps.support.services import create_ticket
from core_apps.support.services.staff_replies import reply_as_staff
from core_apps.support.services.ticket_service_parts.get_ticket_detail import (
    add_ticket_reply,
    TicketClosedConflict,
)

pytestmark = pytest.mark.django_db


def test_console_resolves_general_inquiry_with_explicit_acknowledgment(user, settings):
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    agent = operator("support")
    ticket = create_ticket(
        user,
        "tenant",
        "other",
        "General product feedback",
        "Please review this feedback.",
    )
    client = Client()
    client.force_login(agent)
    url = reverse("admin:support_ticket_change", args=[ticket.pk])
    payload = {
        "service_action": "resolve",
        "acknowledge_resolution": "on",
        "reply": "The general inquiry is answered; no domain obligation changed.",
        "expected_revision": ticket.revision,
        "request_key": str(uuid.uuid4()),
        "_save": "Save",
    }
    assert client.post(url, payload).status_code == 302
    ticket.refresh_from_db()
    assert ticket.status == "resolved"
    assert ticket.revision == 2
    assert TicketMessage.objects.filter(ticket=ticket, sender="support").count() == 1


@pytest.fixture
def general_inquiry(user):
    return create_ticket(
        user,
        "tenant",
        "other",
        "Product feedback",
        "Please review this general question.",
    ), operator("support")


def resolve(ticket, agent, **changes):
    return reply_as_staff(
        **{
            "user": agent,
            "ticket_id": ticket.id,
            "body": "General question answered; no domain effect.",
            "expected_revision": 1,
            "request_key": "resolve-original",
            "resolve_inquiry": True,
            "acknowledge_resolution": True,
            **changes,
        }
    )


def test_resolution_replays_original_and_rejects_new_terminal_mutations(
    general_inquiry,
):
    ticket, agent = general_inquiry
    result = resolve(ticket, agent)
    assert resolve(ticket, agent)[:2] == result[:2]
    assert result[0]["effect"] == "inquiry_resolved"
    ticket.refresh_from_db()
    assert ticket.status == "resolved" and ticket.revision == 2
    with pytest.raises(RentalConflict):
        resolve(ticket, agent, expected_revision=2, request_key="new-resolution")
    with pytest.raises(RentalConflict):
        resolve(
            ticket,
            agent,
            expected_revision=2,
            request_key="new-reply",
            resolve_inquiry=False,
        )
    with pytest.raises(TicketClosedConflict):
        add_ticket_reply(ticket.user, str(ticket.id), "Late customer reply")
    assert ticket.messages.count() == 2
    assert (
        RentalAuditEvent.objects.filter(
            subject_id=ticket.id, action="support.resolve"
        ).count()
        == 1
    )
    event = PlanningEvent.objects.get(recipient=ticket.user)
    assert event.event_key.startswith("support.resolve:")
    assert event.destination["target_id"] == str(ticket.id)
    assert "General question" not in str(event.destination)


@pytest.mark.parametrize(
    "change",
    [
        {"category": "payment"},
        {"category": "verification"},
        {"category": "property"},
        {"category": "visit"},
        {"category": "report_owner"},
        {"category": "report_tenant"},
        {"rental_context": {"subject_id": "protected-canonical-case"}},
        {"reference": "PRIVACY-protected-request"},
    ],
)
def test_general_resolution_does_not_close_domain_or_retention_cases(
    general_inquiry, change
):
    ticket, agent = general_inquiry
    for field, value in change.items():
        setattr(ticket, field, value)
    ticket.save(update_fields=list(change))
    with pytest.raises(RentalConflict) as error:
        resolve(ticket, agent)
    assert error.value.get_codes() == "domain_resolution_required"
    ticket.refresh_from_db()
    assert ticket.status == "open" and ticket.revision == 1
    assert ticket.messages.count() == 1
    assert not PlanningEvent.objects.exists()


def test_resolution_requires_acknowledgment_note_current_revision_and_authority(
    general_inquiry,
):
    ticket, agent = general_inquiry
    for change in [{"acknowledge_resolution": False}, {"body": " "}]:
        with pytest.raises(ValidationError):
            resolve(ticket, agent, **change)
    with pytest.raises(RentalConflict):
        resolve(ticket, agent, expected_revision=99)
    with pytest.raises(PermissionDenied):
        resolve(ticket, ticket.user)
    agent.staff_profile.is_active = False
    agent.staff_profile.save()
    with pytest.raises(PermissionDenied):
        resolve(ticket, agent)
    ticket.refresh_from_db()
    assert ticket.revision == 1 and ticket.messages.count() == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("same_operation", [True, False])
def test_concurrent_resolution_and_reply_serialize_without_duplicate_effects(
    general_inquiry, same_operation
):
    if connection.vendor != "postgresql":
        pytest.skip("Independent PostgreSQL row locking is required")
    ticket, agent = general_inquiry
    start = Barrier(2)

    def command(second):
        close_old_connections()
        try:
            start.wait(timeout=10)
            changes = (
                {}
                if same_operation or not second
                else {
                    "resolve_inquiry": False,
                    "request_key": "competing-reply",
                }
            )
            try:
                return "ok", resolve(ticket, agent, **changes)
            except RentalConflict:
                return "conflict", None
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(command, [False, True]))
    assert sorted(r[0] for r in results) == (
        ["ok", "ok"] if same_operation else ["conflict", "ok"]
    )
    ticket.refresh_from_db()
    assert ticket.revision == 2 and ticket.messages.count() == 2
    assert PlanningEvent.objects.filter(recipient=ticket.user).count() == 1
    if same_operation:
        assert ticket.status == "resolved"
    else:
        assert ticket.status in {"resolved", "in_progress"}
