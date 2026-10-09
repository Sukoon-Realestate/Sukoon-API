import hashlib
import json
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from ..models import (
    BillingPeriod,
    InvoiceLine,
    InvoicePaymentAllocation,
    LedgerEntry,
    LedgerTransaction,
    OwnerPayable,
    PaymentAttempt,
    PaymentReceipt,
    ProviderWebhookEvent,
    RentInvoice,
    RefundRequest,
)
from .rental_phase2 import RentalConflict, add_months


CAIRO = ZoneInfo("Africa/Cairo")


def cairo_instant(day, at_time=time.min):
    return datetime.combine(day, at_time, tzinfo=CAIRO)


def post_ledger_transaction(
    *, reference, kind, entries, lease=None, invoice=None, attempt=None, metadata=None
):
    debit = sum(item[2] for item in entries if item[1] == LedgerEntry.Direction.DEBIT)
    credit = sum(item[2] for item in entries if item[1] == LedgerEntry.Direction.CREDIT)
    if debit != credit or debit <= 0:
        raise ValidationError(
            "Ledger transaction must contain equal positive debits and credits."
        )
    ledger_transaction, created = LedgerTransaction.objects.get_or_create(
        reference=reference,
        defaults={
            "kind": kind,
            "lease": lease,
            "invoice": invoice,
            "payment_attempt": attempt,
            "metadata": metadata or {},
        },
    )
    if created:
        LedgerEntry.objects.bulk_create(
            [
                LedgerEntry(
                    transaction=ledger_transaction,
                    account=account,
                    direction=direction,
                    amount_minor=amount,
                )
                for account, direction, amount in entries
            ]
        )
    return ledger_transaction


def issue_invoice(period):
    invoice = RentInvoice.objects.filter(billing_period=period).first()
    if invoice:
        return invoice
    invoice = RentInvoice.objects.create(
        lease=period.lease,
        billing_period=period,
        reference=f"RENT-{period.lease.id.hex[:8].upper()}-{period.sequence:03d}",
        due_date=period.due_at.astimezone(CAIRO).date(),
        due_at=period.due_at,
        period_start=period.start,
        period_end_exclusive=period.end_exclusive,
        amount_minor=period.amount_minor,
        charges_minor=period.amount_minor,
        currency=period.currency,
        exponent=period.exponent,
        status=RentInvoice.Status.DUE,
    )
    InvoiceLine.objects.create(
        invoice=invoice,
        line_type="base_rent",
        description="Base rent",
        amount_minor=period.amount_minor,
        source={
            "billing_period_id": str(period.id),
            "starts_on": str(period.start),
            "ends_on_exclusive": str(period.end_exclusive),
        },
    )
    period.status = BillingPeriod.Status.ISSUED
    period.save(update_fields=["status", "updated_at"])
    post_ledger_transaction(
        reference=f"invoice-issued:{invoice.id}",
        kind="invoice_issued",
        lease=period.lease,
        invoice=invoice,
        entries=[
            ("tenant_receivable", LedgerEntry.Direction.DEBIT, period.amount_minor),
            (
                "unearned_rent_liability",
                LedgerEntry.Direction.CREDIT,
                period.amount_minor,
            ),
        ],
    )
    return invoice


def generate_billing_schedule(lease):
    if lease.billing_periods.exists():
        return lease.billing_periods.all()
    starts_on = lease.start_date
    ends_on = lease.end_date
    activation = lease.activated_at or timezone.now()
    handover_on = lease.terms.get("handover_on", str(starts_on))
    if isinstance(handover_on, str):
        handover_on = datetime.strptime(handover_on, "%Y-%m-%d").date()
    sequence = 1
    cursor = starts_on
    periods = []
    while cursor < ends_on:
        next_anchor = min(add_months(starts_on, sequence), ends_on)
        if sequence == 1:
            issue_at = activation
            handover_deadline = cairo_instant(handover_on, time.max)
            due_at = min(activation + timedelta(hours=48), handover_deadline)
            if due_at <= activation:
                raise RentalConflict(
                    "The agreed handover window is no longer practical.",
                    code="document_changed",
                )
        else:
            issue_at = cairo_instant(cursor) - timedelta(days=7)
            due_at = cairo_instant(cursor, time.max)
        period = BillingPeriod.objects.create(
            lease=lease,
            sequence=sequence,
            start=cursor,
            end_exclusive=next_anchor,
            issue_at=issue_at,
            due_at=due_at,
            amount_minor=lease.rent_amount_minor,
        )
        periods.append(period)
        cursor = next_anchor
        sequence += 1
    if periods:
        issue_invoice(periods[0])
    return lease.billing_periods.all()


def invoice_balance_minor(invoice):
    return max(invoice.charges_minor - invoice.credits_minor - invoice.applied_minor, 0)


def quote_fingerprint(invoice, request_key, amount_minor, expires_at):
    payload = {
        "invoice_id": str(invoice.id),
        "invoice_revision": invoice.revision,
        "request_key": str(request_key),
        "amount_minor": amount_minor,
        "currency": invoice.currency,
        "expires_at": expires_at.isoformat(),
        "policy_version": "rental-policy-v1",
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def payment_attempt_payload(attempt):
    invoice = attempt.invoice
    receipt = getattr(attempt, "receipt", None)
    allocation = getattr(attempt, "invoice_allocation", None)
    refundable = allocation.amount_minor if allocation else 0
    if refundable:
        reserved = sum(
            attempt.refund_requests.exclude(
                status__in=[RefundRequest.Status.REJECTED, RefundRequest.Status.FAILED]
            ).values_list("amount_minor", flat=True)
        )
        refundable = max(refundable - reserved, 0)
    return {
        "refundable_balance": {
            "amount_minor": refundable,
            "currency": attempt.currency,
            "exponent": attempt.exponent,
        },
        "revision": attempt.revision,
        "lease_id": str(invoice.lease.id),
        "payment_attempt_id": str(attempt.id),
        "invoice_id": str(invoice.id),
        "request_key": str(attempt.request_key),
        "quote_id": str(attempt.quote.id),
        "invoice_revision": attempt.invoice_revision,
        "policy_version": attempt.policy_version,
        "quote_fingerprint": attempt.quote_fingerprint,
        "payment_status": attempt.payment_status,
        "invoice_status": invoice.status,
        "amount": {
            "amount_minor": attempt.amount_minor,
            "currency": attempt.currency,
            "exponent": attempt.exponent,
        },
        "confirmed_at": (
            attempt.confirmed_at.isoformat() if attempt.confirmed_at else None
        ),
        "receipt_id": str(receipt.id) if receipt else "",
        "payout_status": attempt.payout_status,
        "settlement_status": attempt.settlement_status,
        "updated_at": attempt.updated_at.isoformat(),
    }


def _capture_attempt(attempt):
    if attempt.payment_status == PaymentAttempt.Status.CAPTURED:
        return attempt
    invoice = RentInvoice.objects.select_for_update().get(pk=attempt.invoice_id)
    if attempt.amount_minor != invoice_balance_minor(invoice):
        raise RentalConflict("Captured amount does not match invoice balance.")
    attempt.payment_status = PaymentAttempt.Status.CAPTURED
    attempt.confirmed_at = timezone.now()
    attempt.revision += 1
    attempt.save(
        update_fields=["payment_status", "confirmed_at", "revision", "updated_at"]
    )
    invoice.applied_minor += attempt.amount_minor
    invoice.status = RentInvoice.Status.PAID
    invoice.revision += 1
    invoice.save(update_fields=["applied_minor", "status", "revision", "updated_at"])
    InvoicePaymentAllocation.objects.get_or_create(
        payment_attempt=attempt,
        defaults={"invoice": invoice, "amount_minor": attempt.amount_minor},
    )
    post_ledger_transaction(
        reference=f"payment-captured:{attempt.id}",
        kind="payment_captured",
        lease=invoice.lease,
        invoice=invoice,
        attempt=attempt,
        entries=[
            ("psp_clearing", LedgerEntry.Direction.DEBIT, attempt.amount_minor),
            ("tenant_receivable", LedgerEntry.Direction.CREDIT, attempt.amount_minor),
        ],
    )
    if invoice.invoice_type == RentInvoice.InvoiceType.DEPOSIT:
        post_ledger_transaction(
            reference=f"deposit-collected:{attempt.id}",
            kind="deposit_collected",
            lease=invoice.lease,
            invoice=invoice,
            attempt=attempt,
            entries=[
                (
                    "unearned_rent_liability",
                    LedgerEntry.Direction.DEBIT,
                    attempt.amount_minor,
                ),
                (
                    "deposit_liability",
                    LedgerEntry.Direction.CREDIT,
                    attempt.amount_minor,
                ),
            ],
        )
        agreement = getattr(invoice, "deposit_agreement", None)
        if agreement:
            agreement.collected_minor += attempt.amount_minor
            agreement.due_minor = max(
                agreement.agreed_minor - agreement.collected_minor, 0
            )
            agreement.revision += 1
            agreement.save()
        receipt, _ = PaymentReceipt.objects.get_or_create(payment_attempt=attempt)
        invoice.receipt_id = receipt.id
        invoice.save(update_fields=["receipt_id", "updated_at"])
        return attempt
    commission = (
        attempt.amount_minor * 1000 // 10000
        if invoice.billing_period and invoice.billing_period.sequence == 1
        else 0
    )
    net = attempt.amount_minor - commission
    entries = [
        ("unearned_rent_liability", LedgerEntry.Direction.DEBIT, attempt.amount_minor),
        ("owner_liability", LedgerEntry.Direction.CREDIT, net),
    ]
    if commission:
        entries.append(("commission_reserve", LedgerEntry.Direction.CREDIT, commission))
    post_ledger_transaction(
        reference=f"payment-allocated:{attempt.id}",
        kind="payment_allocated",
        lease=invoice.lease,
        invoice=invoice,
        attempt=attempt,
        entries=entries,
    )
    OwnerPayable.objects.get_or_create(
        invoice=invoice,
        defaults={
            "lease": invoice.lease,
            "payment_attempt": attempt,
            "billing_period": invoice.billing_period,
            "gross_minor": attempt.amount_minor,
            "commission_minor": commission,
            "net_minor": net,
            "blocking_reasons": [
                "PSP settlement is pending.",
                "Move-in is not accepted.",
            ],
        },
    )
    receipt, _ = PaymentReceipt.objects.get_or_create(payment_attempt=attempt)
    invoice.receipt_id = receipt.id
    invoice.save(update_fields=["receipt_id", "updated_at"])
    if invoice.billing_period:
        invoice.billing_period.status = BillingPeriod.Status.PAID
        invoice.billing_period.save(update_fields=["status", "updated_at"])
    return attempt


def _settle_attempt(attempt):
    if attempt.payment_status != PaymentAttempt.Status.CAPTURED:
        return False
    if attempt.settlement_status == "settled":
        return True
    attempt.settlement_status = "settled"
    attempt.revision += 1
    attempt.save(update_fields=["settlement_status", "revision", "updated_at"])
    post_ledger_transaction(
        reference=f"payment-settled:{attempt.id}",
        kind="payment_settled",
        lease=attempt.invoice.lease,
        invoice=attempt.invoice,
        attempt=attempt,
        entries=[
            ("platform_cash", LedgerEntry.Direction.DEBIT, attempt.amount_minor),
            ("psp_clearing", LedgerEntry.Direction.CREDIT, attempt.amount_minor),
        ],
    )
    OwnerPayable.objects.filter(payment_attempt=attempt).update(
        settlement_status="settled",
        blocking_reasons=["Move-in is not accepted."],
        updated_at=timezone.now(),
    )
    return True


@transaction.atomic
def process_provider_event(event):
    event = (
        ProviderWebhookEvent.objects.select_for_update()
        .select_related("payment_attempt__invoice__lease")
        .get(pk=event.pk)
    )
    if event.processed:
        return event
    attempt = PaymentAttempt.objects.select_for_update().get(
        pk=event.payment_attempt_id
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
        if attempt.payment_status != PaymentAttempt.Status.CAPTURED:
            attempt.payment_status = PaymentAttempt.Status.FAILED
            attempt.failure_code = str(payload.get("failure_code") or "provider_failed")
            attempt.revision += 1
            attempt.save()
        event.processed = True
    elif event.event_type == "payment.chargeback":
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
                reference=f"chargeback:{event.provider_event_id}",
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
            invoice.lease.financial_closure_status = (
                invoice.lease.FinancialClosureStatus.OPEN
            )
            invoice.lease.save(update_fields=["financial_closure_status", "updated_at"])
        event.processed = True
    else:
        raise ValidationError({"type": "Unsupported payment provider event."})
    if event.processed:
        event.processed_at = timezone.now()
        event.save(update_fields=["processed", "processed_at", "updated_at"])
    if event.event_type == "payment.captured":
        for pending in ProviderWebhookEvent.objects.filter(
            payment_attempt=attempt,
            event_type="payment.settled",
            processed=False,
        ).order_by("sequence", "created_at"):
            process_provider_event(pending)
    return event
