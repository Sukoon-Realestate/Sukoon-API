"""Rental phase3: capture attempt."""

from django.utils import timezone
from ...models import (
    BillingPeriod,
    DepositAgreement,
    InvoicePaymentAllocation,
    LedgerEntry,
    Lease,
    OwnerPayable,
    PaymentAttempt,
    PaymentReceipt,
    RentInvoice,
    RentalChange,
)
from ..rental_phase2 import RentalConflict
from .issue_invoice import post_ledger_transaction
from .payment_attempt_payload import (
    invoice_balance_minor,
    _activate_after_initial_capture,
)


def _capture_attempt(attempt):
    if attempt.payment_status in {
        PaymentAttempt.Status.CAPTURED,
        PaymentAttempt.Status.CHARGEDBACK,
    }:
        return attempt
    invoice = RentInvoice.objects.select_for_update().get(pk=attempt.invoice_id)
    lease = Lease.objects.select_for_update().get(pk=invoice.lease_id)
    invoice.lease = lease
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
    allocation, _ = InvoicePaymentAllocation.objects.get_or_create(
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
        allocation.components = {"rent": 0, "deposit": attempt.amount_minor}
        allocation.save(update_fields=["components", "updated_at"])
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
    deposit = (
        DepositAgreement.objects.select_for_update().filter(invoice=invoice).first()
    )
    deposit_minor = min(deposit.due_minor, attempt.amount_minor) if deposit else 0
    rent_minor = attempt.amount_minor - deposit_minor
    if rent_minor < 0 or deposit_minor < 0:
        raise RentalConflict("Invoice allocations do not match the deposit obligation.")
    first_period = invoice.billing_period and invoice.billing_period.sequence == 1
    # A renewal has its own sequence 1. Use its persisted originating change,
    # not client-controlled terms, to avoid charging acquisition a second time.
    continuous_renewal = (
        first_period
        and RentalChange.objects.filter(
            kind=RentalChange.Kind.RENEWAL,
            status=RentalChange.Status.APPLIED,
            result_lease_id=invoice.lease_id,
            lease__tenancy_root_id=invoice.lease.tenancy_root_id,
        ).exists()
    )
    commission = (
        rent_minor * 1000 // 10000 if first_period and not continuous_renewal else 0
    )
    net = rent_minor - commission
    allocation.components = {"rent": rent_minor, "deposit": deposit_minor}
    allocation.save(update_fields=["components", "updated_at"])
    entries = [
        ("unearned_rent_liability", LedgerEntry.Direction.DEBIT, attempt.amount_minor),
        ("owner_liability", LedgerEntry.Direction.CREDIT, net),
    ]
    if commission:
        entries.append(("commission_reserve", LedgerEntry.Direction.CREDIT, commission))
    if deposit_minor:
        entries.append(
            ("deposit_liability", LedgerEntry.Direction.CREDIT, deposit_minor)
        )
        deposit.collected_minor += deposit_minor
        deposit.due_minor -= deposit_minor
        deposit.revision += 1
        deposit.save(
            update_fields=["collected_minor", "due_minor", "revision", "updated_at"]
        )
    post_ledger_transaction(
        reference=f"payment-allocated:{attempt.id}",
        kind="payment_allocated",
        lease=invoice.lease,
        invoice=invoice,
        attempt=attempt,
        entries=entries,
    )
    if rent_minor:
        OwnerPayable.objects.get_or_create(
            payment_attempt=attempt,
            defaults={
                "invoice": invoice,
                "lease": invoice.lease,
                "billing_period": invoice.billing_period,
                "gross_minor": rent_minor,
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
    if (
        (
            lease.status in {Lease.Status.SIGNED, Lease.Status.EXPIRED}
            or (lease.status == Lease.Status.CANCELLED and lease.activated_at is None)
        )
        and invoice.billing_period
        and invoice.billing_period.sequence == 1
    ):
        _activate_after_initial_capture(lease, attempt)
    return attempt
