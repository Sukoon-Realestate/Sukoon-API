"""Replacement captures replenish the original allocation, never a second payout."""

from django.utils import timezone
from ...models import (
    ChargebackReplacementPayment,
    InvoicePaymentAllocation,
    PaymentReceipt,
    RentalChargeback,
    RentInvoice,
)
from ..rental_phase2 import RentalConflict
from ..rental_phase3_parts.issue_invoice import post_ledger_transaction
from .projection import totals


def take_components(item, amount):
    from ..refunds import captured_components

    remaining = dict(captured_components(item.payment_attempt))
    for refund in item.payment_attempt.refund_requests.filter(
        status="succeeded"
    ).exclude(purpose="chargeback_excess"):
        for name in remaining:
            remaining[name] -= refund.allocations.get(name, 0)
    for row in item.replacement_payments.select_related(
        "payment_attempt__invoice_allocation"
    ):
        allocation = getattr(row.payment_attempt, "invoice_allocation", None)
        for name in remaining:
            remaining[name] -= allocation.components.get(name, 0) if allocation else 0
    for row in item.restorations.all():
        for name in remaining:
            remaining[name] -= row.components.get(name, 0)
    # Existing capture allocation funds the disclosed deposit first.
    deposit = min(amount, max(remaining.get("deposit", 0), 0))
    rent = amount - deposit
    if rent > max(remaining.get("rent", 0), 0):
        raise RentalConflict(
            "Original component evidence cannot support this replacement allocation.",
            code="chargeback_allocation_changed",
        )
    return {"rent": rent, "deposit": deposit}


def capture_replacement(attempt, invoice):
    from ..rental_phase3_parts.payment_attempt_payload import invoice_balance_minor
    from .facts import changed, refresh_invoice
    from .refunds import create_excess_refund

    candidates = (
        RentalChargeback.objects.select_for_update()
        .filter(payment_attempt__invoice=invoice)
        .order_by("created_at")
    )
    item = next(
        (
            row
            for row in candidates
            if row.resolved_at is None or attempt.created_at <= row.resolved_at
        ),
        None,
    )
    if item is None:
        return False
    value = totals(item)
    outstanding = max(
        item.invoice_reopened_minor - value["applied"] - value["replacement_captured"],
        0,
    )
    # Prior refund overlap is reconciled against provider restoration, never
    # guessed as a fresh debt. A late capture is retained as refundable excess.
    amount = (
        0
        if value["overlap"] < item.prior_refund_overlap_minor
        else min(attempt.amount_minor, outstanding, invoice_balance_minor(invoice))
    )
    components = take_components(item, amount)
    excess = attempt.amount_minor - amount
    row = ChargebackReplacementPayment.objects.create(
        chargeback=item,
        payment_attempt=attempt,
        amount_minor=amount,
        excess_minor=excess,
    )
    attempt.payment_status, attempt.confirmed_at = "captured", timezone.now()
    attempt.revision += 1
    attempt.save()
    InvoicePaymentAllocation.objects.create(
        payment_attempt=attempt,
        invoice=invoice,
        amount_minor=amount,
        components=components,
    )
    entries = [("psp_clearing", "debit", attempt.amount_minor)]
    entries += [("tenant_receivable", "credit", amount)] if amount else []
    entries += [("chargeback_excess_liability", "credit", excess)] if excess else []
    post_ledger_transaction(
        reference=f"payment-captured:{attempt.id}",
        kind="payment_captured",
        lease=invoice.lease,
        invoice=invoice,
        attempt=attempt,
        entries=entries,
        metadata={
            "chargeback_id": str(item.id),
            "replacement_minor": amount,
            "excess_minor": excess,
        },
    )
    if amount:
        invoice.applied_minor += amount
        refresh_invoice(invoice)
    receipt, _ = PaymentReceipt.objects.get_or_create(payment_attempt=attempt)
    invoice.receipt_id = receipt.id
    invoice.save(update_fields=["receipt_id", "updated_at"])
    if excess:
        row.excess_refund = create_excess_refund(item, attempt, row.id, excess)
        row.save(update_fields=["excess_refund", "updated_at"])
    changed(item, "replacement_captured")
    return True


def refund_source(attempt):
    replacement = getattr(attempt, "chargeback_replacement", None)
    return replacement.chargeback.payment_attempt if replacement else attempt


def can_refund(attempt):
    if attempt.payment_status == "captured":
        replacement = getattr(attempt, "chargeback_replacement", None)
        return not replacement or replacement.chargeback.resolved_at is not None
    item = RentalChargeback.objects.filter(payment_attempt=attempt).first()
    return bool(
        item
        and item.resolved_at
        and item.restorations.filter(invoice_applied_minor__gt=0).exists()
    )


def checkout_allowed(invoice):
    item = pending(invoice)
    if item is None:
        return True
    value = totals(item)
    return (
        value["overlap"] >= item.prior_refund_overlap_minor
        and remaining_capture(item, value) > 0
    )


def pending(invoice):
    return (
        RentalChargeback.objects.filter(
            payment_attempt__invoice=invoice,
            resolved_at__isnull=True,
        )
        .order_by("created_at")
        .first()
    )


def remaining_capture(item, value):
    return max(
        item.invoice_reopened_minor - value["applied"] - value["replacement_captured"],
        0,
    )


def quote_amount(invoice):
    from ..rental_phase3_parts.payment_attempt_payload import invoice_balance_minor

    item = pending(invoice)
    balance = invoice_balance_minor(invoice)
    return min(balance, remaining_capture(item, totals(item))) if item else balance


def quote_disclosure(invoice, amount):
    from ..rental_phase3_parts.payment_attempt_payload import invoice_balance_minor

    item = pending(invoice)
    if item is None:
        return None
    original = min(
        amount, remaining_capture(item, totals(item)), invoice_balance_minor(invoice)
    )
    return {
        "chargeback_id": str(item.id),
        "currency": item.currency,
        "exponent": item.exponent,
        "quote_total_minor": amount,
        "original_funding_minor": original,
        "excess_refund_minor": amount - original,
        "remaining_invoice_minor": invoice_balance_minor(invoice) - original,
    }
