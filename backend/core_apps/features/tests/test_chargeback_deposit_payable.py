"""A deposit-derived owner payable retains the chargeback exposure of its cash source."""

import pytest
from core_apps.features.models import OwnerPayable, RentalChargeback, RentalPayout
from core_apps.features.services.rental_phase3 import process_provider_event
from core_apps.features.tasks import reconcile_approved_payouts
from core_apps.features.tests.test_funded_settlement import (
    funded_exit,
    awaiting_signatures,
    rental_participants,
    propose,
    authenticated,
    command,
    API,
)
from core_apps.features.tests.test_rental_lifecycle_safety import event, operator
from core_apps.features.tests.test_chargeback_resolution import fact, restore


@pytest.fixture
def derived_payable(funded_exit):
    owner, tenant, _, lease, attempt = funded_exit
    result = propose(
        owner,
        lease,
        [
            {
                "type": "deposit_deduction",
                "description": "Synthetic mutually agreed deposit-funded charge",
                "amount": {"amount_minor": 1_000_000},
                "evidence_ids": [],
            }
        ],
    )
    accepted = authenticated(tenant).post(
        API + f"leases/{lease.id}/final-settlement/respond/",
        command(result["revision"], action="accept"),
        format="json",
    )
    assert accepted.status_code == 200, accepted.data
    derived = OwnerPayable.objects.get(lease=lease, payment_attempt__isnull=True)
    assert derived.source_reference and derived.payout_status == "ready"
    assert not lease.refund_requests.exists()
    return lease, attempt, derived, operator("payout_operator")


def reserve(payable, actor):
    return authenticated(actor).post(
        API + "operations/payouts/execute/",
        command(payable_ids=[str(payable.id)]),
        format="json",
    )


@pytest.mark.django_db
@pytest.mark.parametrize("phase", ["reserve_after", "worker_after", "reconcile_after"])
def test_late_deposit_chargeback_blocks_new_and_already_reserved_payout_until_real_funding(
    derived_payable, phase
):
    lease, attempt, payable, actor = derived_payable
    payout = None
    if phase != "reserve_after":
        reserved = reserve(payable, actor)
        assert reserved.status_code == 201, reserved.data
        payout = RentalPayout.objects.get(id=reserved.data["resource"]["id"])
    process_provider_event(event(attempt, "chargeback"))
    if phase == "reserve_after":
        assert reserve(payable, actor).status_code == 409
        assert not RentalPayout.objects.exists()
    elif phase == "worker_after":
        assert reconcile_approved_payouts()["paid"] == 0
        payout.refresh_from_db()
        payable.refresh_from_db()
        assert payout.status == "held" and payable.payout_status == "submitted"
        assert not payout.provider_payout_id
        assert not lease.ledger_transactions.filter(
            reference=f"payout:{payout.id}"
        ).exists()
    else:
        response = authenticated(actor).post(
            API + f"operations/payouts/{payout.id}/reconcile/",
            command(1),
            format="json",
        )
        assert response.status_code == 409
    item = RentalChargeback.objects.get(payment_attempt=attempt)
    fact(item, "decided", outcome="won")
    restore(item)
    if payout is None:
        reserved = reserve(payable, actor)
        assert reserved.status_code == 201, reserved.data
        payout = RentalPayout.objects.get(id=reserved.data["resource"]["id"])
    response = authenticated(actor).post(
        API + f"operations/payouts/{payout.id}/reconcile/",
        command(payout.revision),
        format="json",
    )
    assert response.status_code == 200, response.data
    assert RentalPayout.objects.count() == 1
    assert (
        lease.ledger_transactions.filter(reference=f"payout:{payout.id}").count() == 1
    )
    payable.refresh_from_db()
    assert payable.payout_status == "succeeded"


@pytest.mark.django_db
def test_late_chargeback_does_not_rewrite_already_paid_deposit_derived_history(
    derived_payable,
):
    _, attempt, payable, actor = derived_payable
    reserved = reserve(payable, actor)
    payout = RentalPayout.objects.get(id=reserved.data["resource"]["id"])
    response = authenticated(actor).post(
        API + f"operations/payouts/{payout.id}/reconcile/",
        command(payout.revision),
        format="json",
    )
    assert response.status_code == 200, response.data
    process_provider_event(event(attempt, "chargeback"))
    payable.refresh_from_db()
    payout.refresh_from_db()
    assert payable.payout_status == "succeeded" and payout.status == "paid"
    assert reserve(payable, actor).status_code == 409


@pytest.mark.django_db
def test_manual_reconciliation_rechecks_role_before_locked_financial_effect(
    derived_payable, monkeypatch
):
    from importlib import import_module
    from core_apps.admin_api.models import StaffProfile

    module = import_module(
        "core_apps.features.rental_phase4_views_parts.operations_reconcile_payout"
    )
    lease, _, payable, actor = derived_payable
    reserved = reserve(payable, actor)
    payout = RentalPayout.objects.get(id=reserved.data["resource"]["id"])
    original = module._require_payout_role

    def revoke_after_initial_check(user, *, lock=False):
        result = original(user, lock=lock)
        if not lock:
            StaffProfile.objects.filter(user=user).update(is_active=False)
        return result

    monkeypatch.setattr(module, "_require_payout_role", revoke_after_initial_check)
    response = authenticated(actor).post(
        API + f"operations/payouts/{payout.id}/reconcile/",
        command(payout.revision),
        format="json",
    )
    assert response.status_code == 403, response.data
    payout.refresh_from_db()
    assert payout.status == "created" and not payout.provider_payout_id
    assert not lease.ledger_transactions.filter(
        reference=f"payout:{payout.id}"
    ).exists()
