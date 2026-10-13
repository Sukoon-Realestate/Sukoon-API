"""Settlements: prepare settlement."""

import uuid
from rest_framework.exceptions import ValidationError
from ...models import DepositAgreement, PaymentAttempt
from ..rental_phase2 import RentalConflict
from ..rental_phase3 import invoice_balance_minor
from ..refunds import remaining_components
from .financial_snapshot import CHARGE_TYPES


def prepare_settlement(lease, lines):
    if lease.legacy_read_only:
        raise RentalConflict("Legacy records require reconciliation before settlement.")
    if lease.occupancy_status not in {"returned", "not_started"}:
        raise RentalConflict(
            "Return possession before agreeing the final financial settlement.",
            code="occupancy_not_returned",
        )
    if lease.status not in {"ended", "cancelled"}:
        raise RentalConflict("This tenancy is not ready for final settlement.")
    if lease.disputes.filter(status="open").exists():
        raise RentalConflict(
            "Resolve open disputes before executing settlement.", code="dispute_open"
        )
    if (
        lease.refund_requests.filter(
            status__in=["requested", "approved", "processing"]
        ).exists()
        or PaymentAttempt.objects.filter(
            invoice__lease=lease,
            payment_status__in=["created", "pending", "authorized"],
        ).exists()
    ):
        raise RentalConflict(
            "Reconcile pending financial operations first.",
            code="financial_action_pending",
        )
    invoices = list(
        lease.invoices.exclude(status__in=["cancelled", "written_off"]).order_by(
            "due_date", "pkid"
        )
    )
    balances = {str(x.id): invoice_balance_minor(x) for x in invoices}
    charges, credits = [], []
    deposit = DepositAgreement.objects.filter(lease=lease).first()
    released_deposit_due = 0
    if deposit and deposit.due_minor:
        target = str(deposit.invoice.id)
        released_deposit_due = min(deposit.due_minor, balances.get(target, 0))
        if released_deposit_due:
            credits.append(
                {
                    "invoice_id": target,
                    "amount_minor": released_deposit_due,
                    "type": "deposit_release",
                    "line_id": str(uuid.uuid5(lease.id, "release-uncollected-deposit")),
                }
            )
            balances[target] -= released_deposit_due
    rent_balance = sum(balances.values())
    refund_due = 0
    requested_return = None
    for line in lines:
        amount = line["amount"]["amount_minor"]
        kind = line["type"]
        if kind == "deposit_return":
            if requested_return is not None or amount < 0:
                raise ValidationError(
                    {"lines": "Specify at most one nonnegative deposit return."}
                )
            requested_return = amount
        elif kind == "refund":
            refund_due += abs(amount)
        elif kind in {"credit", "write_off"} or amount < 0:
            if kind not in {"credit", "write_off", "rent_adjustment"}:
                raise ValidationError({"lines": "Charges cannot be negative."})
            credit = abs(amount)
            targets = [line["invoice_id"]] if line.get("invoice_id") else list(balances)
            for target in targets:
                if target not in balances:
                    raise ValidationError(
                        {
                            "invoice_id": "Credit must target an open invoice of this lease."
                        }
                    )
                applied = min(credit, balances[target])
                if applied:
                    credits.append(
                        {
                            "invoice_id": target,
                            "amount_minor": applied,
                            "type": kind,
                            "line_id": line["id"],
                        }
                    )
                    balances[target] -= applied
                    credit -= applied
            if credit:
                raise RentalConflict(
                    "Credits and write-offs cannot exceed the selected unpaid charges.",
                    code="credit_exceeds_balance",
                )
        elif kind in CHARGE_TYPES:
            if amount:
                charges.append(line)
        else:
            raise ValidationError({"lines": "Unsupported settlement line type."})
    charge_amount = sum(x["amount"]["amount_minor"] for x in charges)
    if charge_amount:
        balances["settlement_invoice"] = charge_amount
    deposit = DepositAgreement.objects.filter(lease=lease).first()
    available = (
        max(deposit.collected_minor - deposit.returned_minor - deposit.applied_minor, 0)
        if deposit
        else 0
    )
    deposit_applications = []
    for target in balances:
        applied = min(available, balances[target])
        if applied:
            deposit_applications.append({"invoice_id": target, "amount_minor": applied})
            balances[target] -= applied
            available -= applied
    if requested_return is not None and requested_return != available:
        raise RentalConflict(
            "The deposit return must equal the balance after approved obligations.",
            code="deposit_allocation_conflict",
        )
    refunds = []
    return_left, rent_left = available, refund_due
    for attempt in (
        PaymentAttempt.objects.filter(invoice__lease=lease, payment_status="captured")
        .select_related("invoice")
        .order_by("pkid")
    ):
        components = remaining_components(attempt)
        # Applied deposit is reserved by the plan before allocating its return.
        deposit_return = min(return_left, components["deposit"])
        rent_refund = min(rent_left, components["rent"])
        if deposit_return or rent_refund:
            refunds.append(
                {
                    "payment_attempt_id": str(attempt.id),
                    "allocations": {"rent": rent_refund, "deposit": deposit_return},
                    "amount_minor": rent_refund + deposit_return,
                }
            )
            return_left -= deposit_return
            rent_left -= rent_refund
    if return_left or rent_left:
        raise RentalConflict(
            "The settlement refund must be backed by unreserved original captures.",
            code="refund_exceeds_balance",
        )
    return {
        "charges": charges,
        "credits": credits,
        "deposit_applications": deposit_applications,
        "released_deposit_due_minor": released_deposit_due,
        "refunds": refunds,
        "rent_balance_minor": rent_balance,
        "deposit_to_return_minor": available,
        "refund_due_minor": refund_due,
        "total_due_minor": sum(balances.values()) - available - refund_due,
    }
