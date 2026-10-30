"""Bounded recovery must visit original unchecked Paymob operations first."""

import io
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from django.core.management import call_command
from rest_framework.exceptions import APIException

from core_apps.features.management.commands import reconcile_paymob_payments as command
from core_apps.features.models import (
    CheckoutSession,
    IdempotencyRecord,
    LedgerTransaction,
    PaymobPayment,
    PaymentAttempt,
    PaymentQuote,
    PaymentReceipt,
    RentInvoice,
)
from core_apps.features.services import paymob_client
from core_apps.features.tests.test_rental_phase3 import phase3_lease


pytestmark = pytest.mark.django_db
START = datetime(2026, 1, 2, 12, tzinfo=timezone.utc)


def payment_graph(lease, tenant, label, *, status, reconciled_at=None):
    """Each recovery candidate owns a distinct invoice, quote and attempt."""
    captured = status == "captured"
    invoice = RentInvoice.objects.create(
        lease=lease,
        reference=f"reconcile-fairness-{label}",
        due_date=lease.start_date,
        amount_minor=1000,
        charges_minor=1000,
        applied_minor=1000 if captured else 0,
        status="paid" if captured else "due",
    )
    quote = PaymentQuote.objects.create(
        invoice=invoice,
        request_key=uuid.uuid4(),
        invoice_revision=invoice.revision,
        payer_amount_minor=1000,
        policy_version="rental-policy-v1",
        fingerprint="f" * 64,
        expires_at=START + timedelta(minutes=20),
    )
    attempt = PaymentAttempt.objects.create(
        invoice=invoice,
        payer=tenant,
        quote=quote,
        request_key=uuid.uuid4(),
        invoice_revision=invoice.revision,
        policy_version=quote.policy_version,
        quote_fingerprint=quote.fingerprint,
        payment_status="captured" if captured else "pending",
        amount_minor=1000,
    )
    payment = PaymobPayment.objects.create(
        attempt=attempt,
        reference=f"sukoon:payment:{attempt.id}",
        integration_id="5991528",
        status=status,
        reconciled_at=reconciled_at,
    )
    if captured:
        PaymentReceipt.objects.create(payment_attempt=attempt)
    return payment


def protected_rows():
    models = (
        RentInvoice,
        PaymentQuote,
        PaymentAttempt,
        PaymobPayment,
        PaymentReceipt,
        CheckoutSession,
        IdempotencyRecord,
        LedgerTransaction,
    )
    return {
        model.__name__: list(
            model.objects.order_by("pk").values(
                *[
                    field.attname
                    for field in model._meta.concrete_fields
                    if model is not PaymobPayment or field.name != "reconciled_at"
                ]
            )
        )
        for model in models
    }


@pytest.mark.parametrize("inquiry_unavailable", [False, True], ids=["pending", "api_error"])
def test_limit_one_visits_unchecked_then_oldest_even_when_inquiry_fails(
    phase3_lease, inquiry_unavailable
):
    _, tenant, lease = phase3_lease
    # Create the previously checked row first: the old PostgreSQL ordering
    # continually selected it ahead of both NULL rows after re-timestamping.
    previous = payment_graph(
        lease, tenant, "previous", status="pending", reconciled_at=START
    )
    first = payment_graph(lease, tenant, "first", status="outcome_unknown")
    second = payment_graph(lease, tenant, "second", status="submitting")
    captured = payment_graph(lease, tenant, "captured", status="captured")
    assert first.pk < second.pk
    assert PaymobPayment.objects.exclude(status="captured").filter(
        reconciled_at__isnull=True
    ).count() == 2
    before = protected_rows()
    seen = []

    def observe_original(payment):
        seen.append((payment.pk, payment.attempt_id, payment.reference))
        if inquiry_unavailable:
            raise APIException("Synthetic provider inquiry unavailable")
        return payment.attempt

    # Patch the command's imported binding, so the actual DB query, limit and
    # finally rotation execute without a provider request or capture side effect.
    with patch.object(command, "reconcile", side_effect=observe_original), patch.object(
        paymob_client, "create_intention"
    ) as create_intention:
        for index, expected in enumerate((first, second, previous, first), start=1):
            checked_at = START + timedelta(minutes=index)
            output = io.StringIO()
            with patch.object(command.timezone, "now", return_value=checked_at):
                call_command("reconcile_paymob_payments", limit=1, stdout=output)
            assert len(seen) == index
            assert seen[-1] == (expected.pk, expected.attempt_id, expected.reference)
            expected.refresh_from_db()
            assert expected.reconciled_at == checked_at
            assert PaymobPayment.objects.exclude(status="captured").filter(
                reconciled_at__isnull=True
            ).count() == max(2 - index, 0)
            assert output.getvalue() == (
                f"Reconciled: {int(not inquiry_unavailable)}; "
                f"unresolved: {int(inquiry_unavailable)}. "
                "No new checkout was submitted.\n"
            )
        create_intention.assert_not_called()

    captured.refresh_from_db()
    assert captured.reconciled_at is None
    assert protected_rows() == before
