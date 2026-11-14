"""Sprint 02 negative input matrix for rental commands (A3-02, A4-03, A4-04).

Malformed bodies must return a controlled 400 (or 404 for identities that are
not eligible) with zero domain rows and zero idempotency receipts; valid stale
commands keep conflicting with 409; the historical valid wire contracts work.
"""

import uuid
from datetime import date

import pytest
from django.utils import timezone

from core_apps.features.models import (
    IdempotencyRecord,
    MaintenanceEvent,
    MaintenanceRequest,
    PaymentAttempt,
    PaymentQuote,
    RefundRequest,
    RentalDispute,
    RentalHandover,
    RentInvoice,
)
from core_apps.users.models import User

from .test_rental_phase5 import client_for, phase5_lease  # noqa: F401  (fixture)

# Rental lifecycle routes are deferred in MVP scope (403 mvp_feature_deferred);
# the harness runs these tests with SUKOON_MVP=False.
pytestmark = [pytest.mark.django_db, pytest.mark.mvp_deferred]
API = "/api/v1/features/v1/"
POISON = [None, True, 1.5, [], {}, "oops", -1]


def counts():
    return (
        MaintenanceRequest.objects.count(),
        MaintenanceEvent.objects.count(),
        RentalHandover.objects.count(),
        RentalDispute.objects.count(),
        RefundRequest.objects.count(),
        IdempotencyRecord.objects.count(),
    )


def assert_rejected(response, before, status=400):
    assert response.status_code == status, (
        response.status_code,
        response.content[:300],
    )
    assert counts() == before


def maintenance_body(**overrides):
    return {
        "title": "Water leak",
        "description": "Kitchen pipe",
        "category": "plumbing",
        "priority": "urgent",
        "access_times": ["morning"],
        "evidence_ids": [],
        "request_key": str(uuid.uuid4()),
        "expected_revision": 0,
        **overrides,
    }


MAINTENANCE_INVALID = [
    *[{"expected_revision": value} for value in POISON + [1]],
    {"title": []},
    {"title": 123},
    {"title": "x" * 161},
    {"description": {"a": 1}},
    {"description": "x" * 4001},
    {"category": {"a": 1}},
    {"category": "Plumb ing"},
    {"category": "x" * 41},
    {"priority": "critical"},
    {"priority": None},
    {"access_times": [1]},
    {"access_times": {"a": 1}},
    {"access_times": ["x"] * 11},
    {"access_times": None},
    {"evidence_ids": "x"},
    {"evidence_ids": ["not-a-uuid"]},
    {"evidence_ids": [None]},
    {"evidence_ids": None},
    {"request_key": None},
    {"request_key": ""},
    {"request_key": "k" * 101},
    {"request_key": []},
]


@pytest.mark.parametrize("override", MAINTENANCE_INVALID, ids=repr)
def test_maintenance_create_rejects_malformed_fields_without_writes(
    phase5_lease, override
):
    owner, tenant, lease = phase5_lease
    before = counts()
    response = client_for(tenant).post(
        f"{API}leases/{lease.id}/maintenance-requests/",
        maintenance_body(**override),
        format="json",
    )
    assert_rejected(response, before)


@pytest.mark.parametrize("body", [[], "text", 5])
def test_maintenance_create_rejects_non_object_bodies(phase5_lease, body):
    owner, tenant, lease = phase5_lease
    before = counts()
    response = client_for(tenant).post(
        f"{API}leases/{lease.id}/maintenance-requests/", body, format="json"
    )
    assert_rejected(response, before)


def test_maintenance_legacy_contracts_still_work(phase5_lease):
    owner, tenant, lease = phase5_lease
    client = client_for(tenant)
    url = f"{API}leases/{lease.id}/maintenance-requests/"
    legacy = maintenance_body(access_times="Weekdays after 5pm", expected_revision="0")
    created = client.post(url, legacy, format="json")
    assert created.status_code == 201, created.content
    assert created.data["resource"]["access_times"] == "Weekdays after 5pm"
    replay = client.post(url, legacy, format="json")
    assert replay.status_code == 201
    assert replay.data["resource"]["id"] == created.data["resource"]["id"]
    assert MaintenanceRequest.objects.count() == 1


def _maintenance(phase5_lease):
    owner, tenant, lease = phase5_lease
    created = client_for(tenant).post(
        f"{API}leases/{lease.id}/maintenance-requests/",
        maintenance_body(),
        format="json",
    )
    assert created.status_code == 201, created.content
    return MaintenanceRequest.objects.get(id=created.data["resource"]["id"])


@pytest.mark.parametrize(
    "override",
    [
        *[{"expected_revision": value} for value in POISON],
        {"note": []},
        {"note": 5},
        {"note": "x" * 4001},
        {"request_key": ["k"]},
        {"request_key": "k" * 101},
    ],
    ids=repr,
)
def test_maintenance_action_rejects_malformed_fields(phase5_lease, override):
    item = _maintenance(phase5_lease)
    owner = phase5_lease[0]
    before = counts()
    body = {
        "action": "acknowledge",
        "expected_revision": 1,
        "request_key": str(uuid.uuid4()),
    }
    response = client_for(owner).post(
        f"{API}maintenance-requests/{item.id}/actions/",
        {**body, **override},
        format="json",
    )
    assert_rejected(response, before)
    item.refresh_from_db()
    assert item.revision == 1


@pytest.mark.parametrize(
    "appointment",
    [
        {
            "appointment_at": "2030-01-01T10:00:00",
            "appointment_ends_at": "2030-01-01T11:00:00",
        },
        {
            "appointment_at": "garbage",
            "appointment_ends_at": "2030-01-01T11:00:00+02:00",
        },
        {"appointment_at": 5, "appointment_ends_at": "2030-01-01T11:00:00+02:00"},
        {"appointment_at": "2030-01-01T10:00:00+02:00", "appointment_ends_at": []},
    ],
    ids=repr,
)
def test_maintenance_appointment_requires_aware_datetimes(phase5_lease, appointment):
    item = _maintenance(phase5_lease)
    owner = phase5_lease[0]
    before = counts()
    response = client_for(owner).post(
        f"{API}maintenance-requests/{item.id}/actions/",
        {
            "action": "propose_appointment",
            "expected_revision": 1,
            "request_key": str(uuid.uuid4()),
            **appointment,
        },
        format="json",
    )
    assert_rejected(response, before)


def test_maintenance_valid_stale_command_still_conflicts(phase5_lease):
    item = _maintenance(phase5_lease)
    owner = phase5_lease[0]
    before = counts()
    response = client_for(owner).post(
        f"{API}maintenance-requests/{item.id}/actions/",
        {
            "action": "acknowledge",
            "expected_revision": 7,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert_rejected(response, before, status=409)
    # Fields other actions ignore stay ignored (historical clients send them).
    ok = client_for(owner).post(
        f"{API}maintenance-requests/{item.id}/actions/",
        {
            "action": "acknowledge",
            "expected_revision": "1",
            "request_key": str(uuid.uuid4()),
            "appointment_at": "",
            "cost": None,
        },
        format="json",
    )
    assert ok.status_code == 200, ok.content


def handover_body(**overrides):
    return {
        "kind": "move_in",
        "possession_on": "2026-01-01",
        "condition": "Clean",
        "keys": {"count": 2},
        "meters": [{"label": "electricity", "value": "10"}],
        "inventory": [{"description": "Sofa"}],
        "evidence_ids": [],
        "request_key": str(uuid.uuid4()),
        "expected_revision": 0,
        **overrides,
    }


HANDOVER_INVALID = [
    *[{"expected_revision": value} for value in POISON + [1]],
    {"kind": "sideways"},
    {"kind": []},
    {"possession_on": "not-a-date"},
    {"possession_on": 20260101},
    {"possession_on": None},
    {"condition": 5},
    {"condition": True},
    {"condition": None},
    {"keys": [1, 2]},
    {"meters": "text"},
    {"inventory": 5},
    {"inventory": [[[[[["too deep"]]]]]]},
    {"meters": [{"value": "x" * 20_000}]},
    {"evidence_ids": None},
    {"evidence_ids": ["x"]},
    {"evidence_ids": [str(uuid.uuid4())] * 6},
    {"request_key": None},
]


@pytest.mark.parametrize("override", HANDOVER_INVALID, ids=repr)
def test_handover_create_rejects_malformed_fields_without_writes(
    phase5_lease, override
):
    owner, tenant, lease = phase5_lease
    before = counts()
    response = client_for(owner).post(
        f"{API}leases/{lease.id}/handovers/", handover_body(**override), format="json"
    )
    assert_rejected(response, before)


def test_handover_update_and_respond_typed_and_stale_conflicts(phase5_lease):
    owner, tenant, lease = phase5_lease
    created = client_for(owner).post(
        f"{API}leases/{lease.id}/handovers/", handover_body(), format="json"
    )
    assert created.status_code == 201, created.content
    handover_id = created.data["resource"]["id"]
    before = counts()
    for override in [
        {"expected_revision": "oops"},
        {"possession_on": "x"},
        {"meters": 5},
    ]:
        response = client_for(owner).patch(
            f"{API}handovers/{handover_id}/",
            {"request_key": str(uuid.uuid4()), "expected_revision": 1, **override},
            format="json",
        )
        assert_rejected(response, before)
    stale = client_for(owner).patch(
        f"{API}handovers/{handover_id}/",
        {"request_key": str(uuid.uuid4()), "expected_revision": 9, "condition": "Good"},
        format="json",
    )
    assert_rejected(stale, before, status=409)
    for body in [
        {
            "action": "accept",
            "request_key": str(uuid.uuid4()),
            "expected_revision": "oops",
        },
        {
            "action": ["accept"],
            "request_key": str(uuid.uuid4()),
            "expected_revision": 1,
        },
        {
            "action": "accept",
            "request_key": str(uuid.uuid4()),
            "expected_revision": 1,
            "note": [],
        },
    ]:
        response = client_for(tenant).post(
            f"{API}handovers/{handover_id}/respond/", body, format="json"
        )
        assert_rejected(response, before)
    stale = client_for(tenant).post(
        f"{API}handovers/{handover_id}/respond/",
        {"action": "accept", "request_key": str(uuid.uuid4()), "expected_revision": 5},
        format="json",
    )
    assert_rejected(stale, before, status=409)


def test_dispute_commands_typed_without_writes(phase5_lease):
    owner, tenant, lease = phase5_lease
    item = _maintenance(phase5_lease)
    valid = {
        "lease_id": str(lease.id),
        "subject_kind": "maintenance",
        "subject_id": str(item.id),
        "reason": "Not fixed",
        "evidence_ids": [],
        "request_key": str(uuid.uuid4()),
        "expected_revision": 0,
    }
    before = counts()
    for override in [{"lease_id": "x"}, {"lease_id": None}, {"lease_id": 5}]:
        # Authority precedence is unchanged: an unusable lease id is 404.
        response = client_for(tenant).post(
            f"{API}disputes/", {**valid, **override}, format="json"
        )
        assert_rejected(response, before, status=404)
    for override in [
        {"subject_id": 5},
        {"subject_kind": []},
        {"evidence_ids": [None]},
        {"reason": []},
        {"reason": "x" * 4001},
        {"request_key": None},
        {"expected_revision": "oops"},
    ]:
        response = client_for(tenant).post(
            f"{API}disputes/", {**valid, **override}, format="json"
        )
        assert_rejected(response, before)
    created = client_for(tenant).post(f"{API}disputes/", valid, format="json")
    assert created.status_code == 201, created.content
    dispute_id = created.data["resource"]["id"]
    before = counts()
    for body in [
        {"request_key": str(uuid.uuid4()), "expected_revision": "oops", "note": "x"},
        {"request_key": str(uuid.uuid4()), "expected_revision": 1, "note": {}},
        {"request_key": str(uuid.uuid4()), "expected_revision": 1, "action": ["reply"]},
    ]:
        response = client_for(owner).post(
            f"{API}disputes/{dispute_id}/respond/", body, format="json"
        )
        assert_rejected(response, before)
    stale = client_for(owner).post(
        f"{API}disputes/{dispute_id}/respond/",
        {"request_key": str(uuid.uuid4()), "expected_revision": 3, "note": "x"},
        format="json",
    )
    assert_rejected(stale, before, status=409)


def test_checkout_command_typed_before_any_lookup(phase5_lease):
    owner, tenant, lease = phase5_lease
    invoice_id = uuid.uuid4()
    valid = {
        "invoice_id": str(invoice_id),
        "quote_id": str(uuid.uuid4()),
        "request_key": str(uuid.uuid4()),
        "expected_revision": 1,
    }
    before = counts()
    for override in [{"expected_revision": value} for value in POISON] + [
        {"quote_id": "bad"},
        {"request_key": 5},
        {"invoice_id": []},
    ]:
        response = client_for(tenant).post(
            f"{API}rent-invoices/{invoice_id}/checkout/",
            {**valid, **override},
            format="json",
        )
        assert_rejected(response, before)


def _purchase_attempt(payer, reference):
    invoice = RentInvoice.objects.create(
        lease=None,
        purpose="subscription",
        payer=payer,
        business_reference=f"subscription:{reference}",
        reference=reference,
        due_date=date(2026, 1, 1),
        due_at=timezone.now(),
        amount_minor=50_000,
        status=RentInvoice.Status.PAID,
    )
    quote = PaymentQuote.objects.create(
        invoice=invoice,
        request_key=uuid.uuid4(),
        invoice_revision=1,
        payer_amount_minor=50_000,
        policy_version="rental-policy-v1",
        fingerprint="e" * 64,
        expires_at=timezone.now(),
    )
    return PaymentAttempt.objects.create(
        invoice=invoice,
        payer=payer,
        quote=quote,
        request_key=uuid.uuid4(),
        invoice_revision=1,
        policy_version="rental-policy-v1",
        quote_fingerprint=quote.fingerprint,
        payment_status=PaymentAttempt.Status.CAPTURED,
        amount_minor=50_000,
    )


def refund_body(attempt_id, **overrides):
    return {
        "payment_attempt_id": str(attempt_id),
        "amount": {"amount_minor": 1000, "currency": "EGP", "exponent": 2},
        "reason": "Overpaid",
        "request_key": str(uuid.uuid4()),
        "expected_revision": 0,
        **overrides,
    }


def test_refund_requests_select_only_rental_attempts(phase5_lease):
    """A4-04: non-rental attempts were an AttributeError 500; now 404."""
    owner, tenant, lease = phase5_lease
    stranger = User.objects.create_user(
        email="p5-stranger@example.com", password="pass", is_verified=True
    )
    own_purchase = _purchase_attempt(tenant, "S02-SUB-OWN")
    other_purchase = _purchase_attempt(stranger, "S02-SUB-OTHER")
    before = counts()
    client = client_for(tenant)
    for attempt_id in (own_purchase.id, other_purchase.id, uuid.uuid4()):
        response = client.post(
            f"{API}refund-requests/", refund_body(attempt_id), format="json"
        )
        assert_rejected(response, before, status=404)
    for attempt_id in ("not-a-uuid", None, 5):
        response = client.post(
            f"{API}refund-requests/",
            refund_body(own_purchase.id, payment_attempt_id=attempt_id),
            format="json",
        )
        assert_rejected(response, before, status=404)
    from .test_rental_phase6 import captured_payment

    _invoice, rental_attempt, _payable = captured_payment(
        lease, tenant, reference="S02-TYPED"
    )
    before = counts()
    for override in [
        {"reason": []},
        {"payment_revision": "oops"},
        {"lease_id": 7},
        {"expected_revision": "0"},
        {"request_key": "not-a-uuid"},
    ]:
        response = client.post(
            f"{API}refund-requests/",
            refund_body(rental_attempt.id, **override),
            format="json",
        )
        assert_rejected(response, before)
    # Identical status for both purposes: no existence or ownership oracle.
    assert (
        client.post(
            f"{API}refund-requests/", refund_body(other_purchase.id), format="json"
        ).data
        == client.post(
            f"{API}refund-requests/", refund_body(uuid.uuid4()), format="json"
        ).data
    )


def test_valid_rental_refund_request_still_created(phase5_lease):
    from .test_rental_phase6 import captured_payment

    owner, tenant, lease = phase5_lease
    _invoice, attempt, _payable = captured_payment(lease, tenant, reference="S02-RENT")
    response = client_for(tenant).post(
        f"{API}refund-requests/",
        refund_body(
            attempt.id, lease_id=str(lease.id), payment_revision=attempt.revision
        ),
        format="json",
    )
    assert response.status_code == 201, response.content
    assert RefundRequest.objects.filter(payment_attempt=attempt).count() == 1


@pytest.mark.parametrize(
    "override",
    [
        {"expected_revision": "oops"},
        {"expected_revision": True},
        {"lease_revision": []},
        {"request_key": "k" * 101},
        {"request_key": ["k"]},
    ],
    ids=repr,
)
def test_change_collection_revisions_are_typed(phase5_lease, override):
    owner, tenant, lease = phase5_lease
    before = counts()
    body = {
        "request_key": str(uuid.uuid4()),
        "expected_revision": 0,
        "lease_revision": lease.revision,
        "reason": "Update",
        **override,
    }
    response = client_for(owner).post(
        f"{API}leases/{lease.id}/amendments/", body, format="json"
    )
    assert_rejected(response, before)


def test_session_revoked_while_waiting_for_lock_rejects_command(phase5_lease):
    """Original claims are rechecked after the lease lock (Sprint 02 epoch story)."""
    from unittest.mock import patch

    from rest_framework.test import APIClient

    from core_apps.features.services import personal_maintenance as commands
    from core_apps.users.services.sessions import issue_refresh, revoke_all

    owner, tenant, lease = phase5_lease
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {issue_refresh(tenant).access_token}"
    )
    original = commands.lease_for

    def revoke_then_lock(actor, lease_id, lock=False, **kwargs):
        if lock:
            revoke_all(tenant)
        return original(actor, lease_id, lock=lock, **kwargs)

    before = counts()
    with patch.object(commands, "lease_for", side_effect=revoke_then_lock):
        response = client.post(
            f"{API}leases/{lease.id}/maintenance-requests/",
            maintenance_body(),
            format="json",
        )
    assert response.status_code == 401, response.content
    assert counts()[:2] == before[:2]
    assert not IdempotencyRecord.objects.filter(
        operation__startswith="maintenance."
    ).exists()


__all__ = ["phase5_lease"]
