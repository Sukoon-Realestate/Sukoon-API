"""Both admin deployments use this real ticket contract; no UserReport stand-ins."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from django.db import close_old_connections, connection
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient
from core_apps.admin_api.models import StaffProfile
from core_apps.common.idempotency import IdempotencyConflict
from core_apps.features.models import LedgerTransaction
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.support.models import (
    Ticket,
    TicketMessage,
    TicketInternalNote,
    TicketTransition,
)
from core_apps.support.services import create_ticket
from core_apps.support.services import operations
from core_apps.users.models import User

pytestmark = pytest.mark.django_db


def operator(name, role="support"):
    user = User.objects.create_user(
        email=f"{name}@example.invalid", password="local-test-password", is_staff=True
    )
    StaffProfile.objects.create(user=user, role_name=role)
    return user


@pytest.fixture
def inquiry(user):
    return create_ticket(
        user,
        "tenant",
        "other",
        "Actual support inquiry",
        "Please help with this general inquiry.",
    )


def client(user):
    value = APIClient()
    value.force_authenticate(user)
    return value


def command(ticket, actor, action="claim", revision=1, **kwargs):
    return operations.command(
        actor,
        ticket.id,
        {
            "action": action,
            "expected_revision": revision,
            "reason": "Documented support transition",
            **kwargs,
        },
        str(uuid.uuid4()),
    )


def test_real_ticket_list_reply_reload_and_private_notes(inquiry, user):
    agent = operator("real-support")
    api = client(agent)
    listing = api.get(reverse("admin-support-list"))
    assert listing.status_code == 200
    assert listing.data["results"][0]["id"] == str(inquiry.id)
    url = reverse("admin-support-detail", args=[inquiry.id])
    body = {
        "action": "reply",
        "body": "Saved reply visible after reload.",
        "reason": "Reply",
        "expected_revision": 1,
    }
    key = str(uuid.uuid4())
    assert (
        api.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY=key).status_code == 200
    )
    assert (
        api.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY=key).status_code == 200
    )
    assert TicketMessage.objects.filter(ticket=inquiry, sender="support").count() == 1
    assert api.get(url).data["messages"][-1]["body"] == body["body"]
    internal = {
        "action": "note",
        "reason": "Private operational note",
        "expected_revision": 2,
    }
    assert (
        api.post(
            url, internal, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4())
        ).status_code
        == 200
    )
    assert api.get(url).data["internal_notes"][0]["body"] == internal["reason"]
    consumer = client(user).get(reverse("support-ticket-detail", args=[inquiry.id]))
    assert consumer.status_code == 200
    assert "Private operational note" not in str(consumer.data)
    assert not LedgerTransaction.objects.exists()


def test_escalation_requires_supervisor_and_one_responsible_operator(inquiry):
    agent, other = operator("first"), operator("second")
    manager = operator("supervisor", "support_supervisor")
    command(inquiry, agent)
    with pytest.raises(RentalConflict):
        command(inquiry, other)
    command(inquiry, agent, "escalate", 2)
    inquiry.refresh_from_db()
    assert inquiry.escalated and inquiry.assigned_to is None
    with pytest.raises(PermissionDenied):
        command(inquiry, other, revision=3)
    command(inquiry, manager, revision=3)
    inquiry.refresh_from_db()
    assert inquiry.assigned_to == manager
    assert list(
        inquiry.transitions.order_by("revision").values_list("action", flat=True)
    ) == ["claim", "escalate", "claim"]
    forbidden = client(agent).post(
        reverse("admin-support-detail", args=[inquiry.id]),
        {
            "action": "reply",
            "body": "Not the responsible operator",
            "reason": "Reply",
            "expected_revision": 4,
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )
    assert forbidden.status_code == 403


def test_current_role_and_financial_authority_are_separate(inquiry):
    agent = operator("revoked")
    StaffProfile.objects.filter(user=agent).update(is_active=False)
    assert (
        client(agent)
        .get(reverse("admin-support-detail", args=[inquiry.id]))
        .status_code
        == 403
    )
    financial = operator("financial", "payout_operator")
    assert (
        client(financial)
        .get(reverse("admin-support-detail", args=[inquiry.id]))
        .status_code
        == 403
    )
    owner = operator("owner", "system_owner")
    assert (
        client(owner)
        .get(reverse("admin-support-detail", args=[inquiry.id]))
        .status_code
        == 200
    )


def test_receipt_recovery_and_absence_fence_prevent_late_replies(inquiry):
    agent = operator("receipt")
    api = client(agent)
    key = str(uuid.uuid4())
    receipt = reverse("admin-support-receipt", args=[inquiry.id, key])
    assert api.get(receipt, {"action": "claim"}).data["status"] == "unknown"
    assert (
        api.post(receipt, {"action": "claim"}, format="json").data["status"]
        == "absent_final"
    )
    with pytest.raises(IdempotencyConflict):
        operations.command(
            agent,
            inquiry.id,
            {"action": "claim", "reason": "Late attempt", "expected_revision": 1},
            key,
        )
    assert not TicketTransition.objects.filter(ticket=inquiry).exists()
    key = str(uuid.uuid4())
    payload = {"action": "note", "reason": "Original note", "expected_revision": 1}
    operations.command(agent, inquiry.id, payload, key)
    assert (
        api.get(
            reverse("admin-support-receipt", args=[inquiry.id, key]), {"action": "note"}
        ).data["status"]
        == "confirmed"
    )
    with pytest.raises(IdempotencyConflict):
        operations.command(
            agent, inquiry.id, {**payload, "reason": "Changed note"}, key
        )
    assert TicketInternalNote.objects.filter(ticket=inquiry).count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_supervisors_claim_one_escalated_ticket(user):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock evidence requires PostgreSQL")
    ticket = create_ticket(
        user, "account", "other", "Account inquiry", "A real account question."
    )
    Ticket.objects.filter(pk=ticket.pk).update(escalated=True)
    actors = [
        operator("supervisor-a", "support_supervisor"),
        operator("supervisor-b", "support_supervisor"),
    ]
    barrier = Barrier(2)

    def claim(actor):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            command(ticket, actor)
            return "claimed"
        except RentalConflict:
            return "changed"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(claim, actors))
    assert sorted(outcomes) == ["changed", "claimed"]
    assert ticket.transitions.count() == 1
