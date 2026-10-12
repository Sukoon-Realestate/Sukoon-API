"""Allocate refunds to captured funds; never infer a partial deposit/rent split."""

from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from ..models import (
    DepositAgreement,
    Lease,
    LedgerTransaction,
    OwnerPayable,
    PaymentAttempt,
    RefundRequest,
    RentInvoice,
)
from ..providers import get_rental_provider
from .rental_phase2 import RentalConflict
from .rental_phase3 import invoice_balance_minor, post_ledger_transaction


def captured_components(attempt):
    allocation = getattr(attempt, "invoice_allocation", None)
    if not allocation:
        return {"rent": 0, "deposit": 0}
    if allocation.components:
        return allocation.components
    # Backward compatible interpretation of the old single, full capture.
    invoice = attempt.invoice
    deposit = (
        allocation.amount_minor
        if invoice.invoice_type == "deposit"
        else sum(
            invoice.lines.filter(line_type="security_deposit").values_list(
                "amount_minor", flat=True
            )
        )
    )
    deposit = min(allocation.amount_minor, max(deposit, 0))
    return {"rent": allocation.amount_minor - deposit, "deposit": deposit}


def remaining_components(attempt, *, exclude_refund=None):
    remaining = dict(captured_components(attempt))
    refunds = attempt.refund_requests.exclude(status__in=["rejected", "failed"])
    if exclude_refund:
        refunds = refunds.exclude(pk=exclude_refund.pk)
    for refund in refunds:
        split = refund.allocations
        if not split:
            # Legacy refunds without a split were rent-only, or a full reversal.
            deposit = (
                remaining["deposit"]
                if refund.amount_minor == sum(remaining.values())
                else 0
            )
            split = {"rent": refund.amount_minor - deposit, "deposit": deposit}
        for component in ("rent", "deposit"):
            remaining[component] -= split.get(component, 0)
    deposit = DepositAgreement.objects.filter(invoice=attempt.invoice).first()
    if deposit:
        pending = RefundRequest.objects.filter(
            payment_attempt__invoice=attempt.invoice,
            status__in=["requested", "approved", "processing"],
        )
        if exclude_refund:
            pending = pending.exclude(pk=exclude_refund.pk)
        reserved_deposit = sum(x.allocations.get("deposit", 0) for x in pending)
        remaining["deposit"] = min(
            remaining["deposit"],
            max(
                deposit.collected_minor
                - deposit.returned_minor
                - deposit.applied_minor
                - reserved_deposit,
                0,
            ),
        )
    return {key: max(value, 0) for key, value in remaining.items()}


def validate_allocations(attempt, amount, allocations=None, *, exclude_refund=None):
    remaining = remaining_components(attempt, exclude_refund=exclude_refund)
    if type(amount) is not int or amount <= 0 or amount > sum(remaining.values()):
        raise RentalConflict(
            "Refund exceeds the remaining captured funds.",
            code="refund_exceeds_balance",
        )
    if not allocations:
        if amount == sum(remaining.values()):
            allocations = remaining
        elif not remaining["deposit"]:
            allocations = {"rent": amount, "deposit": 0}
        elif not remaining["rent"]:
            allocations = {"rent": 0, "deposit": amount}
        else:
            raise RentalConflict(
                "A partial combined refund requires rent and deposit allocations.",
                code="refund_allocation_required",
            )
    if (
        not isinstance(allocations, dict)
        or set(allocations) != {"rent", "deposit"}
        or any(type(value) is not int or value < 0 for value in allocations.values())
        or sum(allocations.values()) != amount
    ):
        raise ValidationError(
            {
                "allocations": "Supply nonnegative integer rent and deposit amounts whose sum equals amount_minor."
            }
        )
    if any(allocations[key] > remaining[key] for key in remaining):
        raise RentalConflict(
            "An allocation exceeds the unreserved captured component.",
            code="refund_exceeds_balance",
        )
    return dict(allocations)


@transaction.atomic
def execute_refund(refund):
    # Shared lease lock orders settlement, refunds, capture and payouts consistently.
    lease = Lease.objects.select_for_update().get(pk=refund.lease_id)
    refund = RefundRequest.objects.select_for_update().get(pk=refund.pk)
    if refund.status != RefundRequest.Status.APPROVED:
        return refund
    attempt = PaymentAttempt.objects.select_for_update().get(
        pk=refund.payment_attempt_id
    )
    invoice = RentInvoice.objects.select_for_update().get(pk=attempt.invoice_id)
    if attempt.payment_status != PaymentAttempt.Status.CAPTURED:
        raise RentalConflict(
            "Only a confirmed capture can be refunded.", code="payment_not_captured"
        )
    split = validate_allocations(
        attempt, refund.amount_minor, refund.allocations, exclude_refund=refund
    )
    payable = (
        OwnerPayable.objects.select_for_update().filter(payment_attempt=attempt).first()
    )
    if (
        payable
        and payable.payout_status in {"submitted", "processing"}
        and split["rent"]
    ):
        raise RentalConflict(
            "Reconcile the in-flight owner payout before refunding rent.",
            code="payout_pending",
        )
    deposit = (
        DepositAgreement.objects.select_for_update().filter(invoice=invoice).first()
    )
    if split["deposit"] and not deposit:
        raise RentalConflict("The captured deposit agreement is missing.")
    commission = 0
    if payable and split["rent"]:
        previous = attempt.refund_requests.filter(status="succeeded")
        original_commission = payable.commission_minor
        if payable.payout_status != "succeeded":
            original_commission += (
                previous.aggregate(total=Sum("commission_reversal_minor"))["total"] or 0
            )
        original_rent = captured_components(attempt)["rent"]
        returned_rent = sum(
            item.allocations.get("rent", item.amount_minor) for item in previous
        )
        already_reversed = (
            previous.aggregate(total=Sum("commission_reversal_minor"))["total"] or 0
        )
        cumulative = int(
            (
                Decimal(original_commission)
                * Decimal(returned_rent + split["rent"])
                / Decimal(original_rent)
            ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        commission = max(
            min(cumulative - already_reversed, original_commission - already_reversed),
            0,
        )
    owner_amount = split["rent"] - commission
    distributed = bool(payable and payable.payout_status == "succeeded")
    refund.provider_refund_id = get_rental_provider().execute_refund(
        refund.id, refund.request_key
    )
    refund.allocations = split
    refund.commission_reversal_minor = commission
    refund.owner_recovery_minor = owner_amount if distributed else 0
    refund.status = RefundRequest.Status.SUCCEEDED
    refund.failure_code = ""
    refund.revision += 1
    refund.save()
    cash_account = (
        "platform_cash" if attempt.settlement_status == "settled" else "psp_clearing"
    )
    entries = [(cash_account, "credit", refund.amount_minor)]
    if split["deposit"]:
        entries.append(("deposit_liability", "debit", split["deposit"]))
        deposit.returned_minor += split["deposit"]
        if refund.purpose == "payment_reversal":
            deposit.due_minor += split["deposit"]
        deposit.revision += 1
        deposit.save()
    if owner_amount:
        entries.append(
            (
                "owner_receivable" if distributed else "owner_liability",
                "debit",
                owner_amount,
            )
        )
    if commission:
        earned = LedgerTransaction.objects.filter(
            reference=f"commission-earned:{payable.id}"
        ).exists()
        entries.append(
            (
                "commission_revenue" if earned else "commission_reserve",
                "debit",
                commission,
            )
        )
    post_ledger_transaction(
        reference=f"refund:{refund.id}",
        kind="refund",
        lease=lease,
        invoice=invoice,
        attempt=attempt,
        entries=entries,
        metadata={
            "allocations": split,
            "purpose": refund.purpose,
            "provider_refund_id": refund.provider_refund_id,
            "commission_reversal_minor": commission,
            "cash_account": cash_account,
        },
    )
    invoice.applied_minor -= refund.amount_minor
    if refund.purpose == "settlement":
        # Agreed release of the charge accompanies the refund; no phantom debt.
        invoice.credits_minor += refund.amount_minor
    else:
        # Restore both the unpaid charge and its deferred liability.
        post_ledger_transaction(
            reference=f"refund-charge-restored:{refund.id}",
            kind="refund_charge_restored",
            lease=lease,
            invoice=invoice,
            entries=[
                ("tenant_receivable", "debit", refund.amount_minor),
                ("unearned_rent_liability", "credit", refund.amount_minor),
            ],
        )
    invoice.status = (
        "paid"
        if invoice_balance_minor(invoice) == 0
        else ("partially_paid" if invoice.applied_minor else "due")
    )
    invoice.revision += 1
    invoice.save()
    if payable and not distributed and split["rent"]:
        payable.gross_minor -= split["rent"]
        payable.net_minor -= owner_amount
        payable.commission_minor -= commission
        payable.payout_status = "cancelled" if payable.net_minor == 0 else "held"
        payable.blocking_reasons = (
            []
            if payable.net_minor == 0
            else ["Refund executed; payout eligibility will be recalculated."]
        )
        payable.revision += 1
        payable.save()
    from ..rental_phase4_views import evaluate_owner_payables
    from .rental_phase6 import evaluate_financial_closure

    evaluate_owner_payables(lease)
    evaluate_financial_closure(lease)
    return refund
