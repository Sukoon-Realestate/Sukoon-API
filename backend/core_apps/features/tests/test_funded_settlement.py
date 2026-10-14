import uuid

import pytest

from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import (
    DepositAgreement,
    LedgerTransaction,
    OwnerPayable,
    RefundRequest,
    RentalHandover,
    RentInvoice,
)
from core_apps.features.services.rental_phase3 import invoice_balance_minor
from core_apps.features.tasks import process_rental_closure
from core_apps.users.models import User
from .test_current_cycle_contract import (
    API,
    awaiting_signatures,
    capture,
    create_checkout,
    sign,
)
from .test_rental_phase2 import authenticated, rental_participants


def command(revision=0, **values):
    return {"request_key": str(uuid.uuid4()), "expected_revision": revision, **values}


@pytest.fixture
def funded_exit(awaiting_signatures):
    owner, tenant, stranger, lease, sessions = awaiting_signatures
    for session in sessions:
        assert sign(session).status_code == 200
    attempt = create_checkout(tenant, lease.invoices.get())
    assert capture(attempt).status_code == 200
    attempt.refresh_from_db()
    settled = authenticated(tenant).post(
        API + f"mock-provider/payment-attempts/{attempt.id}/events/",
        command(attempt.revision, event="settled"),
        format="json",
    )
    assert settled.status_code == 200, settled.data
    # Financial boundary fixture: the separately tested possession/legal cycle ended.
    lease.status = "ended"
    lease.occupancy_status = "returned"
    lease.save()
    (
        lease.inventory_day_locks.all().delete()
        if hasattr(lease, "inventory_day_locks")
        else None
    )
    from core_apps.features.models import RentalInventoryDayLock

    RentalInventoryDayLock.objects.filter(lease=lease).delete()
    RentalHandover.objects.create(
        lease=lease,
        kind="move_in",
        possession_on=lease.start_date,
        status="accepted",
        approvals=[str(owner.id), str(tenant.id)],
    )
    return owner, tenant, stranger, lease, attempt


def propose(owner, lease, lines):
    base = API + f"leases/{lease.id}/final-settlement/"
    initial = authenticated(owner).get(base).data
    response = authenticated(owner).post(
        base + "propose/", command(initial["revision"], lines=lines), format="json"
    )
    assert response.status_code == 200, response.data
    return response.data["resource"]


@pytest.mark.django_db
def test_funded_deposit_deduction_return_and_owner_payout_close(funded_exit):
    owner, tenant, stranger, lease, attempt = funded_exit
    item = propose(
        owner,
        lease,
        [
            {
                "type": "deposit_deduction",
                "description": "Agreed damaged key",
                "amount": {"amount_minor": 200_000},
                "evidence_ids": [],
            }
        ],
    )
    assert item["deposit_to_return"]["amount_minor"] == 800_000
    body = command(item["revision"], action="accept")
    path = API + f"leases/{lease.id}/final-settlement/respond/"
    assert authenticated(stranger).post(path, body, format="json").status_code == 404
    accepted = authenticated(tenant).post(path, body, format="json")
    assert accepted.status_code == 200, accepted.data
    assert accepted.data["resource"]["execution_status"] == "executed"
    assert authenticated(tenant).post(path, body, format="json").data == accepted.data
    assert lease.invoices.filter(invoice_type="adjustment").count() == 1
    deposit = DepositAgreement.objects.get(lease=lease)
    assert deposit.applied_minor == 200_000 and deposit.returned_minor == 0
    assert process_rental_closure()["refunds"] == 1
    assert process_rental_closure()["refunds"] == 0
    deposit.refresh_from_db()
    assert deposit.returned_minor == 800_000
    assert all(invoice_balance_minor(x) == 0 for x in lease.invoices.all())
    lease.refresh_from_db()
    assert lease.financial_closure_status == "open"  # Owner payout still outstanding.
    operator = User.objects.create_user(
        email="settlement-operator@example.test", password="test", is_verified=True
    )
    StaffProfile.objects.create(
        user=operator, role_name=StaffProfile.RoleName.PAYOUT_OPERATOR
    )
    payables = list(lease.owner_payables.all())
    assert sum(x.net_minor for x in payables) == 1_100_000
    payout = authenticated(operator).post(
        API + "operations/payouts/execute/",
        command(payable_ids=[str(x.id) for x in payables]),
        format="json",
    )
    assert payout.status_code == 201, payout.data
    payout_id = payout.data["resource"]["id"]
    assert (
        authenticated(operator)
        .post(
            API + f"operations/payouts/{payout_id}/reconcile/",
            command(1),
            format="json",
        )
        .status_code
        == 200
    )
    process_rental_closure()
    lease.refresh_from_db()
    assert lease.financial_closure_status == "closed"
    for tx in lease.ledger_transactions.all():
        assert sum(x.amount_minor for x in tx.entries.filter(direction="debit")) == sum(
            x.amount_minor for x in tx.entries.filter(direction="credit")
        )


@pytest.mark.django_db
def test_partial_combined_refund_replay_and_component_limits(funded_exit):
    _, tenant, _, lease, attempt = funded_exit
    attempt.refresh_from_db()
    payment = (
        authenticated(tenant)
        .get(API + f"payment-attempts/{attempt.id}/")
        .json()["data"]
    )
    body = command(
        lease_id=str(lease.id),
        payment_attempt_id=str(attempt.id),
        payment_revision=attempt.revision,
        amount={"amount_minor": 500_000, "currency": "EGP", "exponent": 2},
        allocations={"rent": 200_000, "deposit": 300_000},
        reason="Agreed partial refund",
    )
    created = authenticated(tenant).post(API + "refund-requests/", body, format="json")
    assert created.status_code == 201, created.data
    assert (
        authenticated(tenant).post(API + "refund-requests/", body, format="json").data
        == created.data
    )
    too_much_deposit = {
        **body,
        **command(),
        "amount": {"amount_minor": 800_000},
        "allocations": {"rent": 0, "deposit": 800_000},
    }
    assert (
        authenticated(tenant)
        .post(API + "refund-requests/", too_much_deposit, format="json")
        .status_code
        == 409
    )
    operator = User.objects.create_user(
        email="refund-operator@example.test", password="test", is_verified=True
    )
    StaffProfile.objects.create(
        user=operator, role_name=StaffProfile.RoleName.REFUND_OPERATOR
    )
    item = created.data["resource"]
    path = API + f"refund-requests/{item['id']}/"
    approved = authenticated(operator).post(
        path + "respond/", command(1, action="approve"), format="json"
    )
    assert approved.status_code == 200
    execution_body = command(2)
    executed = authenticated(operator).post(
        path + "execute/", execution_body, format="json"
    )
    assert executed.status_code == 200, executed.data
    assert (
        authenticated(operator)
        .post(path + "execute/", execution_body, format="json")
        .data
        == executed.data
    )
    assert RefundRequest.objects.count() == 1
    assert DepositAgreement.objects.get(lease=lease).returned_minor == 300_000
    payable = OwnerPayable.objects.get(payment_attempt=attempt)
    assert payable.net_minor == 720_000 and payable.commission_minor == 80_000
    tx = LedgerTransaction.objects.get(reference=f"refund:{item['id']}")
    assert dict(tx.entries.values_list("account", "amount_minor")) == {
        "platform_cash": 500_000,
        "deposit_liability": 300_000,
        "owner_liability": 180_000,
        "commission_reserve": 20_000,
    }

    import json, os
    from pathlib import Path

    if directory := os.environ.get("SOKOUN_PLANNING_ARTIFACT_DIR"):
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        grant = (
            authenticated(tenant)
            .get(
                API + "rental-capabilities/",
                {"subject_id": str(attempt.id), "action": "create_rental_refund"},
            )
            .json()["data"]
        )
        (target / "django-refund-contract.json").write_text(
            json.dumps(
                {
                    "actor_id": str(tenant.id),
                    "payment": payment,
                    "create_body": body,
                    "created": created.json()["data"],
                    "executed": executed.json()["data"],
                    "grant": grant,
                },
                indent=2,
            )
        )


@pytest.mark.django_db
def test_settlement_refuses_changed_finances_and_applies_explicit_writeoff(funded_exit):
    owner, tenant, _, lease, _ = funded_exit
    debt = RentInvoice.objects.create(
        lease=lease,
        reference="unpaid-exit",
        due_date=lease.end_date,
        amount_minor=200_000,
        charges_minor=200_000,
    )
    item = propose(
        owner,
        lease,
        [
            {
                "type": "write_off",
                "invoice_id": str(debt.id),
                "amount": {"amount_minor": 200_000},
            }
        ],
    )
    debt.revision += 1
    debt.save()
    rejected = authenticated(tenant).post(
        API + f"leases/{lease.id}/final-settlement/respond/",
        command(item["revision"], action="accept"),
        format="json",
    )
    assert rejected.status_code == 409
    assert rejected["X-App-Error-Code"] == "settlement_financial_state_changed"
    assert not RefundRequest.objects.exists()
    item = propose(
        owner,
        lease,
        [
            {
                "type": "write_off",
                "invoice_id": str(debt.id),
                "amount": {"amount_minor": 200_000},
            }
        ],
    )
    accepted = authenticated(tenant).post(
        API + f"leases/{lease.id}/final-settlement/respond/",
        command(item["revision"], action="accept"),
        format="json",
    )
    assert accepted.status_code == 200, accepted.data
    debt.refresh_from_db()
    assert debt.status == "written_off" and debt.credits_minor == 200_000


def approved_refund(tenant, lease, attempt, rent, deposit):
    from core_apps.features.services.refunds import execute_refund

    response = authenticated(tenant).post(
        API + "refund-requests/",
        command(
            lease_id=str(lease.id),
            payment_attempt_id=str(attempt.id),
            amount={"amount_minor": rent + deposit},
            allocations={"rent": rent, "deposit": deposit},
            reason="Boundary test",
        ),
        format="json",
    )
    assert response.status_code == 201, response.data
    item = RefundRequest.objects.get(id=response.data["resource"]["id"])
    item.status = "approved"  # Operations review is covered separately above.
    item.save()
    return execute_refund(item)


@pytest.mark.django_db
def test_partial_refund_can_be_repaid_without_duplicate_owner_or_deposit_allocations(
    funded_exit,
):
    owner, tenant, _, lease, attempt = funded_exit
    lease.status = "active"
    lease.save()
    approved_refund(tenant, lease, attempt, 200_000, 300_000)
    invoice = lease.invoices.get()
    assert (
        invoice.status == "partially_paid" and invoice_balance_minor(invoice) == 500_000
    )
    repayment = create_checkout(tenant, invoice)
    assert capture(repayment).status_code == 200
    assert repayment.invoice_allocation.components == {
        "rent": 200_000,
        "deposit": 300_000,
    }
    deposit = DepositAgreement.objects.get(lease=lease)
    assert deposit.collected_minor - deposit.returned_minor == 1_000_000
    assert deposit.due_minor == 0
    assert sum(x.net_minor for x in lease.owner_payables.all()) == 900_000
    assert lease.owner_payables.count() == 2


@pytest.mark.django_db
def test_settlement_releases_uncollected_deposit_instead_of_paying_it_to_owner(
    funded_exit,
):
    owner, tenant, _, lease, attempt = funded_exit
    approved_refund(tenant, lease, attempt, 0, 300_000)
    item = propose(owner, lease, [])
    assert item["deposit_to_return"]["amount_minor"] == 700_000
    accepted = authenticated(tenant).post(
        API + f"leases/{lease.id}/final-settlement/respond/",
        command(item["revision"], action="accept"),
        format="json",
    )
    assert accepted.status_code == 200, accepted.data
    process_rental_closure()
    deposit = DepositAgreement.objects.get(lease=lease)
    assert (
        deposit.due_minor == 0
        and deposit.returned_minor == 1_000_000
        and deposit.applied_minor == 0
    )
    assert lease.owner_payables.count() == 1
    assert invoice_balance_minor(lease.invoices.get()) == 0


@pytest.mark.django_db
def test_settlement_adjustment_balance_after_deposit_is_payable(funded_exit):
    owner, tenant, _, lease, _ = funded_exit
    item = propose(
        owner,
        lease,
        [
            {
                "type": "claim",
                "description": "Approved restoration",
                "amount": {"amount_minor": 1_250_000},
            }
        ],
    )
    response = authenticated(tenant).post(
        API + f"leases/{lease.id}/final-settlement/respond/",
        command(item["revision"], action="accept"),
        format="json",
    )
    assert response.status_code == 200, response.data
    invoice = lease.invoices.get(invoice_type="adjustment")
    assert (
        invoice.status == "partially_paid" and invoice_balance_minor(invoice) == 250_000
    )
    attempt = create_checkout(tenant, invoice)
    assert capture(attempt).status_code == 200
    invoice.refresh_from_db()
    assert invoice.status == "paid" and invoice_balance_minor(invoice) == 0
    assert OwnerPayable.objects.get(payment_attempt=attempt).net_minor == 250_000
    import json, os
    from pathlib import Path

    if directory := os.environ.get("SOKOUN_PLANNING_ARTIFACT_DIR"):
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        (target / "django-settlement-contract.json").write_text(
            json.dumps(
                {"proposed": item, "accepted": response.json()["data"]}, indent=2
            )
        )


@pytest.mark.django_db
def test_refund_after_owner_payout_requires_explicit_mock_recovery(funded_exit):
    from core_apps.features.rental_phase4_views import evaluate_owner_payables
    from core_apps.features.services.rental_phase6 import closure_blocking_reasons

    owner, tenant, _, lease, attempt = funded_exit
    operator = User.objects.create_superuser(
        email="recovery-admin@example.test", password="test"
    )
    evaluate_owner_payables(lease)
    payable = OwnerPayable.objects.get(payment_attempt=attempt)
    paid = authenticated(operator).post(
        API + "operations/payouts/execute/",
        command(payable_ids=[str(payable.id)]),
        format="json",
    )
    assert paid.status_code == 201, paid.data
    payout_id = paid.data["resource"]["id"]
    assert (
        authenticated(operator)
        .post(
            API + f"operations/payouts/{payout_id}/reconcile/",
            command(1),
            format="json",
        )
        .status_code
        == 200
    )
    refund = approved_refund(tenant, lease, attempt, 200_000, 0)
    payable.refresh_from_db()
    assert payable.net_minor == 900_000 and payable.commission_minor == 100_000
    assert (
        refund.owner_recovery_minor == 180_000
        and refund.commission_reversal_minor == 20_000
    )
    assert any("Owner funds" in x for x in closure_blocking_reasons(lease))
    body = command(
        refund.revision,
        action="confirm_owner_recovery",
        amount={"amount_minor": 180_000},
    )
    path = API + f"refund-requests/{refund.id}/execute/"
    assert authenticated(owner).post(path, body, format="json").status_code == 403
    result = authenticated(operator).post(path, body, format="json")
    assert result.status_code == 200, result.data
    assert authenticated(operator).post(path, body, format="json").data == result.data
    assert not any("Owner funds" in x for x in closure_blocking_reasons(lease))
