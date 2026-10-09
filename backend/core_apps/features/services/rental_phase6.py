from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Sum

from ..models import (
    DepositAgreement,
    FinalSettlement,
    LedgerEntry,
    LedgerTransaction,
    OwnerPayable,
    PaymentAttempt,
    RefundRequest,
    RentInvoice,
    RentalDispute,
    RentalInventoryDayLock,
)
from .rental_phase3 import invoice_balance_minor, post_ledger_transaction
from ..providers import get_rental_provider


def refundable_balance_minor(attempt):
    allocation = getattr(attempt, "invoice_allocation", None)
    captured = allocation.amount_minor if allocation else 0
    reserved = (
        attempt.refund_requests.exclude(
            status__in=[RefundRequest.Status.REJECTED, RefundRequest.Status.FAILED]
        ).aggregate(total=Sum("amount_minor"))["total"]
        or 0
    )
    return max(captured - reserved, 0)


def settlement_balances(lease, lines):
    rent_balance = sum(
        invoice_balance_minor(x)
        for x in lease.invoices.exclude(
            status__in=[RentInvoice.Status.CANCELLED, RentInvoice.Status.WRITTEN_OFF]
        )
    )
    deposit = DepositAgreement.objects.filter(lease=lease).first()
    deposit_return = (
        max(deposit.collected_minor - deposit.returned_minor - deposit.applied_minor, 0)
        if deposit
        else 0
    )
    line_total = sum(int(line["amount"]["amount_minor"]) for line in lines)
    refund_due = max(-line_total, 0)
    total_due = rent_balance + max(line_total, 0) - deposit_return - refund_due
    return rent_balance, deposit_return, refund_due, total_due


def closure_blocking_reasons(lease):
    reasons = []
    if lease.occupancy_status != lease.OccupancyStatus.RETURNED:
        reasons.append("Occupancy has not been returned.")
    if any(
        invoice_balance_minor(x)
        for x in lease.invoices.exclude(
            status__in=[RentInvoice.Status.CANCELLED, RentInvoice.Status.WRITTEN_OFF]
        )
    ):
        reasons.append("An invoice balance remains.")
    deposit = DepositAgreement.objects.filter(lease=lease).first()
    if (
        deposit
        and deposit.collected_minor - deposit.returned_minor - deposit.applied_minor
    ):
        reasons.append("The deposit is unresolved.")
    if lease.refund_requests.filter(
        status__in=[
            RefundRequest.Status.REQUESTED,
            RefundRequest.Status.APPROVED,
            RefundRequest.Status.PROCESSING,
        ]
    ).exists():
        reasons.append("A refund is pending.")
    if lease.disputes.filter(status=RentalDispute.Status.OPEN).exists():
        reasons.append("A dispute is unresolved.")
    if lease.invoices.filter(
        payment_attempts__payment_status=PaymentAttempt.Status.CHARGEDBACK
    ).exists():
        reasons.append("A chargeback is unresolved.")
    if lease.owner_payables.exclude(payout_status="succeeded").exists():
        reasons.append("An owner payable or payout is unresolved.")
    if RentalInventoryDayLock.objects.filter(
        lease=lease, kind=RentalInventoryDayLock.Kind.OCCUPIED
    ).exists():
        reasons.append("Rental inventory has not been returned.")
    settlement = FinalSettlement.objects.filter(lease=lease).first()
    if not settlement or settlement.status != FinalSettlement.Status.ACCEPTED:
        reasons.append("The final settlement is not accepted.")
    return reasons


def evaluate_financial_closure(lease):
    reasons = closure_blocking_reasons(lease)
    desired = (
        lease.FinancialClosureStatus.CLOSED
        if not reasons
        else lease.FinancialClosureStatus.OPEN
    )
    if lease.financial_closure_status != desired:
        lease.financial_closure_status = desired
        lease.revision += 1
        lease.save(update_fields=["financial_closure_status", "revision", "updated_at"])
    return reasons


@transaction.atomic
def execute_refund(refund):
    refund = (
        RefundRequest.objects.select_for_update()
        .select_related("payment_attempt__invoice__lease")
        .get(pk=refund.pk)
    )
    if refund.status == RefundRequest.Status.SUCCEEDED:
        return refund
    if refund.status != RefundRequest.Status.APPROVED:
        return refund
    attempt = PaymentAttempt.objects.select_for_update().get(
        pk=refund.payment_attempt_id
    )
    invoice = RentInvoice.objects.select_for_update().get(pk=attempt.invoice_id)
    provider = get_rental_provider()
    refund.provider_refund_id = provider.execute_refund(refund.id, refund.request_key)
    refund.status = RefundRequest.Status.SUCCEEDED
    refund.revision += 1
    refund.save()
    payable = OwnerPayable.objects.filter(payment_attempt=attempt).first()
    commission_reversal = 0
    if payable and payable.commission_minor:
        commission_reversal = int(
            (
                Decimal(payable.commission_minor)
                * Decimal(refund.amount_minor)
                / Decimal(attempt.amount_minor)
            ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
    owner_reversal = refund.amount_minor - commission_reversal
    entries = [("platform_cash", LedgerEntry.Direction.CREDIT, refund.amount_minor)]
    if owner_reversal:
        entries.append(("owner_liability", LedgerEntry.Direction.DEBIT, owner_reversal))
    if commission_reversal:
        earned = LedgerTransaction.objects.filter(
            reference=f"commission-earned:{payable.id}"
        ).exists()
        entries.append(
            (
                "commission_revenue" if earned else "commission_reserve",
                LedgerEntry.Direction.DEBIT,
                commission_reversal,
            )
        )
    post_ledger_transaction(
        reference=f"refund:{refund.id}",
        kind="refund",
        lease=invoice.lease,
        invoice=invoice,
        attempt=attempt,
        entries=entries,
        metadata={
            "provider_refund_id": refund.provider_refund_id,
            "commission_reversal_minor": commission_reversal,
        },
    )
    invoice.applied_minor = max(invoice.applied_minor - refund.amount_minor, 0)
    invoice.status = (
        RentInvoice.Status.DUE
        if invoice.applied_minor == 0
        else RentInvoice.Status.PARTIALLY_PAID
    )
    invoice.revision += 1
    invoice.save()
    if payable:
        payable.net_minor = max(payable.net_minor - owner_reversal, 0)
        payable.commission_minor = max(
            payable.commission_minor - commission_reversal, 0
        )
        payable.payout_status = "held"
        payable.blocking_reasons = ["A refund changed the payable balance."]
        payable.revision += 1
        payable.save()
    evaluate_financial_closure(invoice.lease)
    return refund
