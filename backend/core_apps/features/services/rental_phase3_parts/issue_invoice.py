"""Rental phase3: issue invoice."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ...models import (
    BillingPeriod,
    DepositAgreement,
    InvoiceLine,
    LedgerEntry,
    LedgerTransaction,
    Lease,
    RentInvoice,
)
from ..rental_phase2 import RentalConflict, add_months


CAIRO = ZoneInfo("Africa/Cairo")


def cairo_instant(day, at_time=time.min):
    return datetime.combine(day, at_time, tzinfo=CAIRO)


@transaction.atomic
def post_ledger_transaction(
    *, reference, kind, entries, lease=None, invoice=None, attempt=None, metadata=None
):
    entries = list(entries)
    if any(
        isinstance(amount, bool)
        or not isinstance(amount, int)
        or amount <= 0
        or direction not in {"debit", "credit"}
        for _, direction, amount in entries
    ):
        raise ValidationError(
            "Ledger entries require positive integer amounts and supported directions."
        )
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
    else:
        expected = sorted(
            (account, direction, amount) for account, direction, amount in entries
        )
        existing = sorted(
            ledger_transaction.entries.values_list(
                "account", "direction", "amount_minor"
            )
        )
        if (
            ledger_transaction.kind != kind
            or ledger_transaction.lease_id != (lease.pk if lease else None)
            or ledger_transaction.invoice_id != (invoice.pk if invoice else None)
            or ledger_transaction.payment_attempt_id
            != (attempt.pk if attempt else None)
            or existing != expected
            or ledger_transaction.metadata != (metadata or {})
        ):
            raise RentalConflict(
                "A ledger source identity cannot be reused for different entries.",
                code="financial_source_conflict",
            )
    return ledger_transaction


@transaction.atomic
def issue_invoice(period):
    period = (
        BillingPeriod.objects.select_for_update()
        .select_related("lease")
        .get(pk=period.pk)
    )
    invoice = RentInvoice.objects.filter(billing_period=period).first()
    if invoice:
        return invoice
    # Only the newly signed workflow combines the first rent and deposit.
    # Historical active leases and their invoice identities stay unchanged.
    combined = period.sequence == 1 and period.lease.status == Lease.Status.SIGNED
    deposit_minor = (
        int(period.lease.terms.get("deposit", {}).get("amount_minor", 0))
        if combined
        else 0
    )
    total = period.amount_minor + deposit_minor
    if combined and DepositAgreement.objects.filter(lease=period.lease).exists():
        raise RentalConflict("A deposit obligation already exists for this agreement.")
    invoice = RentInvoice.objects.create(
        lease=period.lease,
        billing_period=period,
        reference=f"RENT-{period.lease.id.hex[:8].upper()}-{period.sequence:03d}",
        due_date=period.due_at.astimezone(CAIRO).date(),
        due_at=period.due_at,
        period_start=period.start,
        period_end_exclusive=period.end_exclusive,
        amount_minor=total,
        charges_minor=total,
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
    if combined:
        DepositAgreement.objects.create(
            lease=period.lease,
            invoice=invoice,
            agreed_minor=deposit_minor,
            due_minor=deposit_minor,
        )
        if deposit_minor:
            InvoiceLine.objects.create(
                invoice=invoice,
                line_type="security_deposit",
                description="Security deposit",
                amount_minor=deposit_minor,
                source={"lease_id": str(period.lease.id)},
            )
    period.status = BillingPeriod.Status.ISSUED
    period.save(update_fields=["status", "updated_at"])
    post_ledger_transaction(
        reference=f"invoice-issued:{invoice.id}",
        kind="invoice_issued",
        lease=period.lease,
        invoice=invoice,
        entries=[
            ("tenant_receivable", LedgerEntry.Direction.DEBIT, total),
            (
                "unearned_rent_liability",
                LedgerEntry.Direction.CREDIT,
                total,
            ),
        ],
    )
    return invoice


@transaction.atomic
def generate_billing_schedule(lease):
    lease = Lease.objects.select_for_update().get(pk=lease.pk)
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
            due_at = (
                lease.hold_expires_at
                if lease.status == Lease.Status.SIGNED
                else min(activation + timedelta(hours=48), handover_deadline)
            )
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
