"""Rental phase3: process provider event."""

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ...models import (
    LedgerEntry,
    LedgerTransaction,
    Lease,
    OwnerPayable,
    PaymentAttempt,
    ProviderWebhookEvent,
    RentInvoice,
)
from ..rental_phase2 import RentalConflict
from .issue_invoice import post_ledger_transaction
from .capture_attempt import _capture_attempt


def _settle_attempt(attempt):
    if attempt.payment_status != PaymentAttempt.Status.CAPTURED:
        return False
    if attempt.settlement_status == "settled":
        return True
    attempt.settlement_status = "settled"
    attempt.revision += 1
    attempt.save(update_fields=["settlement_status", "revision", "updated_at"])
    refunded_before_settlement = sum(
        tx.entries.filter(account="psp_clearing", direction="credit").aggregate(
            total=Sum("amount_minor")
        )["total"]
        or 0
        for tx in LedgerTransaction.objects.filter(
            payment_attempt=attempt, kind="refund"
        )
    )
    net_settlement = attempt.amount_minor - refunded_before_settlement
    if net_settlement:
        post_ledger_transaction(
            reference=f"payment-settled:{attempt.id}",
            kind="payment_settled",
            lease=attempt.invoice.lease,
            invoice=attempt.invoice,
            attempt=attempt,
            entries=[
                ("platform_cash", LedgerEntry.Direction.DEBIT, net_settlement),
                ("psp_clearing", LedgerEntry.Direction.CREDIT, net_settlement),
            ],
        )
    OwnerPayable.objects.filter(payment_attempt=attempt).update(
        settlement_status="settled",
        blocking_reasons=["Move-in is not accepted."],
        updated_at=timezone.now(),
    )
    from ...rental_phase4_views import evaluate_owner_payables

    evaluate_owner_payables(attempt.invoice.lease)
    return True


@transaction.atomic
def process_provider_event(event):
    # Shared financial roots precede attempt/event locks, including company portfolios.
    lease_id = PaymentAttempt.objects.values_list("invoice__lease_id", flat=True).get(
        pk=event.payment_attempt_id
    )
    if lease_id is None:
        raise RentalConflict(
            "This provider event is not a rental payment.",
            code="invalid_payment_domain",
        )
    from ..rental_lifecycle.locks import lock_financial_lease

    lock_financial_lease(Lease.objects.get(pk=lease_id))
    attempt = PaymentAttempt.objects.select_for_update().get(
        pk=event.payment_attempt_id
    )
    event = ProviderWebhookEvent.objects.select_for_update(of=("self",)).get(
        pk=event.pk
    )
    if event.processed:
        return event
    if not event.signature_valid:
        raise RentalConflict(
            "The provider event has not been authenticated.",
            code="invalid_provider_signature",
        )
    payload = event.payload
    if (
        payload.get("currency") != attempt.currency
        or int(payload.get("amount_minor", -1)) != attempt.amount_minor
    ):
        raise RentalConflict("Provider amount or currency mismatch.")
    if event.event_type == "payment.captured":
        _capture_attempt(attempt)
        event.processed = True
    elif event.event_type == "payment.settled":
        event.processed = _settle_attempt(attempt)
    elif event.event_type == "payment.failed":
        if attempt.payment_status not in {
            PaymentAttempt.Status.CAPTURED,
            PaymentAttempt.Status.CHARGEDBACK,
        }:
            attempt.payment_status = PaymentAttempt.Status.FAILED
            attempt.failure_code = str(payload.get("failure_code") or "provider_failed")
            attempt.revision += 1
            attempt.save()
        event.processed = True
    elif event.event_type == "payment.chargeback":
        # Keep a reversal pending until the original capture is recorded.
        if attempt.payment_status not in {
            PaymentAttempt.Status.CAPTURED,
            PaymentAttempt.Status.CHARGEDBACK,
        }:
            return event
        if attempt.payment_status != PaymentAttempt.Status.CHARGEDBACK:
            amount = int(payload["amount_minor"])
            attempt.payment_status = PaymentAttempt.Status.CHARGEDBACK
            attempt.revision += 1
            attempt.save(update_fields=["payment_status", "revision", "updated_at"])
            invoice = RentInvoice.objects.select_for_update().get(pk=attempt.invoice_id)
            invoice.applied_minor = max(invoice.applied_minor - amount, 0)
            invoice.status = (
                RentInvoice.Status.DUE
                if invoice.applied_minor == 0
                else RentInvoice.Status.PARTIALLY_PAID
            )
            invoice.revision += 1
            invoice.save()
            post_ledger_transaction(
                reference=f"chargeback:{attempt.id}",
                kind="chargeback",
                lease=invoice.lease,
                invoice=invoice,
                attempt=attempt,
                entries=[
                    ("chargeback_receivable", LedgerEntry.Direction.DEBIT, amount),
                    ("platform_cash", LedgerEntry.Direction.CREDIT, amount),
                ],
            )
            OwnerPayable.objects.filter(payment_attempt=attempt).update(
                payout_status="held",
                blocking_reasons=["A chargeback is unresolved."],
                updated_at=timezone.now(),
            )
            from ..rental_phase6 import evaluate_financial_closure

            evaluate_financial_closure(invoice.lease)
            if invoice.lease.renter_company_id:
                from ..company.tenancy_access import notify

                notify(invoice.lease.company_tenancy)
        event.processed = True
    else:
        raise ValidationError({"type": "Unsupported payment provider event."})
    if event.processed:
        event.processed_at = timezone.now()
        event.save(update_fields=["processed", "processed_at", "updated_at"])
    if event.event_type == "payment.captured":
        for pending in ProviderWebhookEvent.objects.filter(
            payment_attempt=attempt,
            event_type__in=["payment.settled", "payment.chargeback"],
            processed=False,
        ).order_by("sequence", "created_at"):
            process_provider_event(pending)
    return event
