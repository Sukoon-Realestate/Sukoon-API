"""C20-T01/T02/T03, X01/X02: original identity, never text matching."""

from datetime import timedelta
import pytest
from django.urls import reverse
from django.utils import timezone
from core_apps.features.models import IdempotencyRecord
from core_apps.support.models import Ticket

pytestmark = pytest.mark.django_db
BODY = {
    "workspace": "tenant",
    "category": "payment",
    "subject": "Payment inquiry",
    "description": "Please help me check my original payment.",
}


def create(client, key, body=None):
    return client.post(
        reverse("support-ticket-list-create"),
        body or BODY,
        format="json",
        HTTP_IDEMPOTENCY_KEY=key,
    )


def lookup(client, key, workspace="tenant"):
    return client.get(
        reverse("support-ticket-creation-receipt"),
        {"workspace": workspace},
        HTTP_IDEMPOTENCY_KEY=key,
    )


def test_lost_response_recovers_exact_ticket_among_identical_inquiries(auth_client):
    first = create(auth_client, "original").json()["data"]
    second = create(auth_client, "separate").json()["data"]
    receipt = lookup(auth_client, "original")
    assert receipt.status_code == 200
    assert receipt["Cache-Control"] == "no-store"
    assert set(receipt.json()) == {"message", "data"}
    assert receipt.json()["data"]["outcome"] == "acknowledged"
    assert receipt.json()["data"]["ticket"]["id"] == first["id"] != second["id"]
    assert Ticket.objects.count() == 2


def test_receipt_is_account_and_workspace_scoped(auth_client, api_client, another_user):
    create(auth_client, "private-key")
    api_client.force_authenticate(another_user)
    for response in [
        lookup(api_client, "private-key"),
        lookup(auth_client, "private-key", "owner"),
    ]:
        assert response.status_code == 200
        assert response.json()["data"] == {
            "outcome": "unknown",
            "request_key": "private-key",
            "ticket": None,
        }


def test_absence_never_claims_safe_resubmission(auth_client):
    assert (
        lookup(auth_client, "not-yet-committed").json()["data"]["outcome"] == "unknown"
    )
    assert Ticket.objects.count() == 0


def test_old_receipt_replays_without_new_ticket(auth_client):
    first = create(auth_client, "old").json()["data"]
    IdempotencyRecord.objects.filter(request_key="old").update(
        created_at=timezone.now() - timedelta(days=90)
    )
    response = create(auth_client, "old")
    assert response.status_code == 201
    assert response.json()["data"]["id"] == first["id"]
    changed = create(auth_client, "old", {**BODY, "subject": "Different intention"})
    assert changed.status_code == 409
    assert Ticket.objects.count() == 1


def test_receipt_requires_authentication(api_client):
    assert lookup(api_client, "key").status_code == 401
