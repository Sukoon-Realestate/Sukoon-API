"""Refunds: remaining components."""

from rest_framework.exceptions import ValidationError
from ...models import DepositAgreement, RefundRequest
from ..rental_phase2 import RentalConflict


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
    chargeback = getattr(attempt, "chargeback", None)
    if chargeback:
        remaining = {"rent": 0, "deposit": 0}
        for row in chargeback.restorations.all():
            for name in remaining:
                remaining[name] += row.components.get(name, 0)
    refunds = attempt.refund_requests.exclude(
        status__in=["rejected", "failed"]
    ).exclude(purpose="chargeback_excess")
    if chargeback:
        refunds = refunds.exclude(
            id__in=chargeback.source_snapshot.get("prior_refund_ids", [])
        )
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
