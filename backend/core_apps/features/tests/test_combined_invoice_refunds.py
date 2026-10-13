import uuid

import pytest

from core_apps.features.models import DepositAgreement, RefundRequest
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.services.rental_phase3 import invoice_payment_allowed
from core_apps.features.services.rental_phase6 import execute_refund
from .test_current_cycle_contract import (
    API,
    awaiting_signatures,
    capture,
    create_checkout,
    sign,
)
from .test_rental_phase2 import authenticated, rental_participants


@pytest.mark.django_db
@pytest.mark.parametrize("full", [True, False])
def test_combined_refund_preserves_rent_deposit_allocation(
    awaiting_signatures, full, monkeypatch
):
    _, tenant, _, lease, sessions = awaiting_signatures
    for session in sessions:
        assert sign(session).status_code == 200
    invoice = lease.invoices.get()
    attempt = create_checkout(tenant, invoice)
    assert capture(attempt).status_code == 200
    if not full:
        rejected = authenticated(tenant).post(
            API + "refund-requests/",
            {
                "lease_id": str(lease.id),
                "payment_attempt_id": str(attempt.id),
                "amount": {"amount_minor": 500_000, "currency": "EGP", "exponent": 2},
                "expected_revision": 0,
                "request_key": str(uuid.uuid4()),
                "reason": "Partial refund",
            },
            format="json",
        )
        assert rejected.status_code == 409
        assert rejected["X-App-Error-Code"] == "refund_allocation_required"
        assert not RefundRequest.objects.exists()
    refund = RefundRequest.objects.create(
        lease=lease,
        payment_attempt=attempt,
        requester=tenant,
        request_key=uuid.uuid4(),
        amount_minor=2_000_000 if full else 500_000,
        refundable_balance_snapshot_minor=2_000_000,
        status=RefundRequest.Status.APPROVED,
        reason="Mock QA refund",
    )
    calls = []
    monkeypatch.setattr(
        "core_apps.features.providers.FakeRentalProvider.execute_refund",
        lambda *args: calls.append(args) or "mock-refund",
    )
    if not full:
        with pytest.raises(RentalConflict, match="allocations"):
            execute_refund(refund)
        assert calls == []
        assert not lease.ledger_transactions.filter(kind="refund").exists()
        return
    execute_refund(refund)
    execute_refund(refund)
    assert len(calls) == 1
    tx = lease.ledger_transactions.get(kind="refund")
    assert dict(tx.entries.values_list("account", "amount_minor")) == {
        "psp_clearing": 2_000_000,
        "deposit_liability": 1_000_000,
        "owner_liability": 900_000,
        "commission_reserve": 100_000,
    }
    assert DepositAgreement.objects.get(lease=lease).returned_minor == 1_000_000
    invoice.refresh_from_db()
    assert invoice.applied_minor == 0
    assert invoice_payment_allowed(tenant, invoice)
