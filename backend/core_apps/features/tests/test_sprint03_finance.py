"""Sprint 03 money recovery, typed handovers and read-only catalogs."""

import uuid
from unittest.mock import patch

import pytest
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext

from core_apps.features.models import (
    FinalSettlement,
    LedgerTransaction,
    OwnerPayable,
    RentalDocument,
    RentalHandover,
)
from core_apps.features.services.payable_eligibility import evaluate_owner_payables
from core_apps.features.services.refunds import execute_refund
from .test_current_cycle_contract import awaiting_signatures
from .test_rental_phase2 import rental_participants, authenticated
from . import test_funded_settlement as funding_fixtures
from .test_funded_settlement import approved_refund, command, API
from . import test_rental_phase4 as handover_fixtures
from .test_rental_phase4 import client_for
from . import test_paymob_invoice_payments as provider_fixtures

funded_exit = funding_fixtures.funded_exit
phase4_lease = handover_fixtures.phase4_lease
phase3_lease = provider_fixtures.phase3_lease
paymob = provider_fixtures.paymob

pytestmark = [pytest.mark.django_db, pytest.mark.mvp_deferred]


def assert_balanced(lease):
    for item in lease.ledger_transactions.all():
        assert sum(x.amount_minor for x in item.entries.filter(direction="debit")) == sum(
            x.amount_minor for x in item.entries.filter(direction="credit")
        )


@pytest.mark.parametrize("recognized_first", [True, False])
def test_repeated_split_partial_and_full_refund_preserve_recognition(funded_exit, recognized_first):
    owner, tenant, _, lease, attempt = funded_exit
    if recognized_first:
        with transaction.atomic():
            evaluate_owner_payables(lease)
    payable = OwnerPayable.objects.get(payment_attempt=attempt)
    reference = f"commission-earned:{payable.id}"
    initial_entries = (
        list(
            LedgerTransaction.objects.get(reference=reference).entries.values_list(
                "account", "direction", "amount_minor"
            )
        )
        if recognized_first
        else None
    )
    one = approved_refund(tenant, lease, attempt, 100_000, 200_000)
    two = approved_refund(tenant, lease, attempt, 200_000, 300_000)
    # Original retries never dispatch another provider instruction or rewrite facts.
    with patch(
        "core_apps.features.services.rental_lifecycle.provider_instructions.execute_local_instruction"
    ) as send:
        execute_refund(one)
        execute_refund(two)
    send.assert_not_called()
    payable.refresh_from_db()
    assert (payable.gross_minor, payable.commission_minor, payable.net_minor) == (
        700_000,
        70_000,
        630_000,
    )
    recognized = LedgerTransaction.objects.get(reference=reference)
    if recognized_first:
        assert (
            list(recognized.entries.values_list("account", "direction", "amount_minor"))
            == initial_entries
        )
    else:
        assert recognized.entries.get(account="commission_reserve").amount_minor == 90_000
    rest = approved_refund(tenant, lease, attempt, 700_000, 500_000)
    assert rest.commission_reversal_minor == 70_000
    payable.refresh_from_db()
    assert (
        payable.gross_minor,
        payable.commission_minor,
        payable.net_minor,
        payable.payout_status,
    ) == (0, 0, 0, "cancelled")
    assert LedgerTransaction.objects.filter(reference=reference).count() == 1
    assert_balanced(lease)


@pytest.mark.parametrize("purpose", ["subscription", "advertising", "maintenance", "promotion"])
def test_unsupported_refund_domain_is_authorized_not_found(funded_exit, purpose):
    _, tenant, stranger, lease, attempt = funded_exit
    invoice = attempt.invoice
    invoice.lease = None
    invoice.purpose = purpose
    invoice.payer = tenant
    invoice.business_reference = f"sprint03:{purpose}:{invoice.id}"
    invoice.save()
    count = lease.refund_requests.count()
    for actor in (tenant, stranger):
        response = authenticated(actor).post(
            API + "refund-requests/",
            command(payment_attempt_id=str(attempt.id)),
            format="json",
        )
        assert response.status_code == 404
    assert lease.refund_requests.count() == count


@pytest.mark.parametrize(
    "identity,expected", [("not-a-uuid", 404), (str(uuid.uuid4()), 404), (None, 404)]
)
def test_invalid_refund_identity_is_defined(phase4_lease, identity, expected):
    _, tenant, _ = phase4_lease
    response = client_for(tenant).post(
        API + "refund-requests/", command(payment_attempt_id=identity), format="json"
    )
    assert response.status_code == expected


@pytest.mark.parametrize(
    "field,value",
    [
        ("possession_on", None),
        ("possession_on", "2026-02-30"),
        ("expected_revision", True),
        ("expected_revision", "no"),
        ("condition", None),
        ("keys", []),
        ("meters", "invalid"),
        ("inventory", "invalid"),
        ("evidence_ids", None),
    ],
)
def test_invalid_handover_commands_do_not_write(phase4_lease, field, value):
    owner, _, lease = phase4_lease
    body = command(
        kind="move_in",
        possession_on=str(lease.start_date),
        condition={},
        keys={},
        meters={},
        inventory=[],
        evidence_ids=[],
    )
    body[field] = value
    response = client_for(owner).post(API + f"leases/{lease.id}/handovers/", body, format="json")
    assert response.status_code == 400, response.data
    assert not RentalHandover.objects.exists()


def test_document_catalog_and_absent_settlement_get_are_read_only(phase4_lease):
    owner, _, lease = phase4_lease
    lease.document_id = uuid.uuid4()
    lease.save()
    with CaptureQueriesContext(connection) as queries:
        docs = client_for(owner).get(API + f"leases/{lease.id}/documents/")
        draft = client_for(owner).get(API + f"leases/{lease.id}/final-settlement/")
        again = client_for(owner).get(API + f"leases/{lease.id}/final-settlement/")
    assert docs.status_code == draft.status_code == 200
    assert docs.data["count"] == 0
    assert draft.data["id"] is None and draft.data["revision"] == 1 and draft.data == again.data
    assert not RentalDocument.objects.exists() and not FinalSettlement.objects.exists()
    assert not any(
        q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for q in queries
    )


def test_historical_document_backfill_is_explicit_idempotent_and_pageable(phase4_lease):
    from core_apps.features.services.document_intents import backfill

    owner, _, lease = phase4_lease
    lease.document_id = uuid.uuid4()
    lease.save()
    backfill(lease)
    backfill(lease)
    assert RentalDocument.objects.count() == 1
    for number in range(25):
        RentalDocument.objects.create(
            lease=lease, title=f"Statement {number}", document_type="statement"
        )
    first = client_for(owner).get(API + f"leases/{lease.id}/documents/?page_size=10")
    assert first.data["count"] == 26 and len(first.data["results"]) == 10 and first.data["next"]
    second = client_for(owner).get(first.data["next"])
    assert not {x["id"] for x in first.data["results"]} & {x["id"] for x in second.data["results"]}


@pytest.mark.django_db(transaction=True)
def test_confirmed_provider_proof_repairs_recognized_partial_refund_without_resubmission(
    phase3_lease, paymob
):
    from core_apps.features.models import OwnerPaymentProfile, PaymobRefund
    from core_apps.features.services import paymob_client, paymob_refunds
    from core_apps.features.services.rental_phase2 import RentalConflict
    from core_apps.features.services.rental_phase3_parts.process_provider_event import (
        _settle_attempt,
    )
    from . import test_paymob_invoice_payments as provider

    paymob.PAYMOB_REFUNDS_ENABLED = True
    payment = provider.captured_payment(phase3_lease)
    lease = payment.attempt.invoice.lease
    OwnerPaymentProfile.objects.create(
        owner=lease.owner,
        payout_ready=True,
        accepted_policy_versions=["rental-policy-v1"],
    )
    RentalHandover.objects.create(
        lease=lease, kind="move_in", status="accepted", possession_on=lease.start_date
    )
    with transaction.atomic():
        _settle_attempt(payment.attempt)
    payable = OwnerPayable.objects.get(payment_attempt=payment.attempt)
    recognition = LedgerTransaction.objects.get(reference=f"commission-earned:{payable.id}")
    original = list(recognition.entries.values_list("account", "direction", "amount_minor"))
    refund = provider.approved_refund(payment)
    instruction = PaymobRefund.objects.get(refund=refund)
    with patch.object(
        paymob_client,
        "inquiry",
        side_effect=[
            provider.snapshot(payment, refunded_amount_cents=0),
            provider.refund_proof(payment),
        ],
    ), patch.object(paymob_client, "submit_refund", return_value={"id": 999}) as submit:
        with patch(
            "core_apps.features.services.refunds.execute_refund",
            side_effect=RentalConflict("transient accounting failure"),
        ):
            with pytest.raises(RentalConflict):
                paymob_refunds.process(instruction)
        assert submit.call_count == 1
    instruction.refresh_from_db()
    assert instruction.status == "confirmed" and instruction.failure_code == "accounting_pending"
    with patch.object(paymob_client, "submit_refund") as submit, patch.object(
        paymob_client, "inquiry"
    ) as inquire:
        repaired = paymob_refunds.process(instruction)
        paymob_refunds.process(instruction)
    submit.assert_not_called()
    inquire.assert_not_called()
    assert repaired.status == "succeeded"
    assert list(recognition.entries.values_list("account", "direction", "amount_minor")) == original
    payable.refresh_from_db()
    assert payable.commission_minor == 99_000 and payable.net_minor == 891_000
    assert LedgerTransaction.objects.filter(reference=f"refund:{refund.id}").count() == 1
    assert_balanced(lease)
