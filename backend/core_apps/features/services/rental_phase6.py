from ..models import (
    DepositAgreement,
    FinalSettlement,
    Lease,
    PaymentAttempt,
    RefundRequest,
    RentInvoice,
    RentalDispute,
    RentalInventoryDayLock,
)
from .rental_phase3 import invoice_balance_minor
from .refunds import execute_refund, remaining_components  # noqa: F401


def refundable_balance_minor(attempt):
    return sum(remaining_components(attempt).values())


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
    if lease.status not in {Lease.Status.ENDED, Lease.Status.CANCELLED}:
        reasons.append("The legal agreement has not ended.")
    if lease.invoices.filter(
        payment_attempts__payment_status__in=["created", "pending", "authorized"]
    ).exists():
        reasons.append("A payment is still awaiting reconciliation.")
    if lease.occupancy_status not in [
        lease.OccupancyStatus.RETURNED,
        lease.OccupancyStatus.NOT_STARTED,
    ]:
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
    if lease.owner_payables.exclude(
        payout_status__in=["succeeded", "cancelled"]
    ).exists():
        reasons.append("An owner payable or payout is unresolved.")
    if any(
        x.owner_recovery_minor > x.owner_recovered_minor
        for x in lease.refund_requests.all()
    ):
        reasons.append("Owner funds must be recovered after a refunded payout.")
    if RentalInventoryDayLock.objects.filter(
        lease=lease, kind=RentalInventoryDayLock.Kind.OCCUPIED
    ).exists():
        reasons.append("Rental inventory has not been returned.")

    settlement = FinalSettlement.objects.filter(lease=lease).first()
    has_accepted_settlement = (
        settlement and settlement.status == FinalSettlement.Status.ACCEPTED
    )

    # Defined financial-closure policy for cancelled never-occupied records:
    # A never-occupied cancelled draft with zero financial transactions/obligations
    # (no invoice balance, no collected deposit, no pending refunds, no disputes,
    # no unresolved payables, no chargebacks) requires no final settlement.
    # If any financial activity exists, final settlement / resolution remains required.
    has_financial_activity = (
        lease.invoices.exclude(
            status__in=[RentInvoice.Status.CANCELLED, RentInvoice.Status.WRITTEN_OFF]
        ).exists()
        or (deposit and deposit.collected_minor > 0)
        or lease.refund_requests.exists()
        or lease.disputes.exists()
        or lease.owner_payables.exists()
    )
    is_cancelled_clean_unoccupied = (
        lease.status == lease.Status.CANCELLED
        and lease.occupancy_status == lease.OccupancyStatus.NOT_STARTED
        and not has_financial_activity
    )

    if (
        settlement
        and settlement.execution_plan
        and settlement.execution_status != "executed"
    ):
        reasons.append("Settlement execution is incomplete.")
    if not has_accepted_settlement and not is_cancelled_clean_unoccupied:
        reasons.append("The final settlement is not accepted.")
    return reasons


def evaluate_financial_closure(lease, *, increment_revision=True):
    """Persist derived closure state, normally as a new lease revision.

    A caller that already increments the locked lease in the same transaction
    can include closure in that mutation by passing increment_revision=False.
    """
    reasons = closure_blocking_reasons(lease)
    desired = (
        lease.FinancialClosureStatus.CLOSED
        if not reasons
        else lease.FinancialClosureStatus.OPEN
    )
    if lease.financial_closure_status != desired:
        lease.financial_closure_status = desired
        fields = ["financial_closure_status", "updated_at"]
        if increment_revision:
            lease.revision += 1
            fields.append("revision")
        lease.save(update_fields=fields)
    return reasons
