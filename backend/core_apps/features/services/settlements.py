"""Versioned settlement consent and auditable execution of its financial plan."""

import uuid

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from ..models import (
    DepositAgreement,
    FinalSettlement,
    InvoiceLine,
    Lease,
    OwnerPayable,
    PaymentAttempt,
    RefundRequest,
    RentInvoice,
)
from .rental_phase2 import RentalConflict, fingerprint
from .rental_phase3 import invoice_balance_minor, post_ledger_transaction
from .refunds import remaining_components


CHARGE_TYPES = {
    "rent",
    "utility",
    "claim",
    "deposit_deduction",
    "damage",
    "cleaning",
    "utilities",
    "rent_adjustment",
}
LINE_TYPES = CHARGE_TYPES | {"deposit_return", "refund", "credit", "write_off"}


def financial_snapshot(lease):
    deposit = DepositAgreement.objects.filter(lease=lease).first()
    return {
        "invoices": [
            {
                "id": str(x.id),
                "revision": x.revision,
                "balance": invoice_balance_minor(x),
            }
            for x in lease.invoices.exclude(
                status__in=["cancelled", "written_off"]
            ).order_by("pkid")
        ],
        "deposit": (
            {"id": str(deposit.id), "revision": deposit.revision} if deposit else None
        ),
        "payments": list(
            PaymentAttempt.objects.filter(invoice__lease=lease)
            .order_by("pkid")
            .values("pkid", "revision", "payment_status", "settlement_status")
        ),
        "refunds": list(
            lease.refund_requests.order_by("pkid").values("pkid", "revision", "status")
        ),
        "payables": list(
            lease.owner_payables.order_by("pkid").values(
                "pkid", "revision", "payout_status", "net_minor"
            )
        ),
        "disputes": list(
            lease.disputes.order_by("pkid").values("pkid", "revision", "status")
        ),
    }


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


def _apply_credit(lease, item, credit, index):
    invoice = RentInvoice.objects.select_for_update().get(
        id=credit["invoice_id"], lease=lease
    )
    amount = credit["amount_minor"]
    if amount > invoice_balance_minor(invoice):
        raise RentalConflict(
            "Invoice balance changed after settlement consent.",
            code="settlement_financial_state_changed",
        )
    invoice.credits_minor += amount
    invoice.status = (
        "written_off"
        if credit["type"] == "write_off" and invoice_balance_minor(invoice) == 0
        else ("paid" if invoice_balance_minor(invoice) == 0 else invoice.status)
    )
    invoice.revision += 1
    invoice.save()
    InvoiceLine.objects.create(
        invoice=invoice,
        line_type=credit["type"],
        description="Agreed final settlement credit",
        amount_minor=-amount,
        source={"settlement_id": str(item.id), "line_id": credit["line_id"]},
    )
    post_ledger_transaction(
        reference=f"settlement-credit:{item.id}:{index}",
        kind="settlement_credit",
        lease=lease,
        invoice=invoice,
        entries=[
            ("unearned_rent_liability", "debit", amount),
            ("tenant_receivable", "credit", amount),
        ],
    )


@transaction.atomic
def execute_settlement(item):
    lease = Lease.objects.select_for_update().get(pk=item.lease_id)
    item = FinalSettlement.objects.select_for_update().get(pk=item.pk)
    if item.execution_status == "executed":
        return item
    if item.status != "accepted":
        raise RentalConflict("Both participants must accept the current settlement.")
    if not item.financial_snapshot or fingerprint(
        item.financial_snapshot
    ) != fingerprint(financial_snapshot(lease)):
        raise RentalConflict(
            "Financial records changed; propose a fresh settlement for both parties to review.",
            code="settlement_financial_state_changed",
        )
    plan = item.execution_plan
    for index, credit in enumerate(plan["credits"]):
        _apply_credit(lease, item, credit, index)
    adjustment = None
    if plan["charges"]:
        total = sum(line["amount"]["amount_minor"] for line in plan["charges"])
        adjustment = RentInvoice.objects.create(
            lease=lease,
            reference=f"SET-{item.id.hex}",
            invoice_type="adjustment",
            due_date=timezone.localdate(),
            due_at=timezone.now(),
            amount_minor=total,
            charges_minor=total,
            status="due",
        )
        for line in plan["charges"]:
            InvoiceLine.objects.create(
                invoice=adjustment,
                line_type=line["type"],
                description=line.get("description")
                or line.get("label")
                or line["type"],
                amount_minor=line["amount"]["amount_minor"],
                source={"settlement_id": str(item.id), "line_id": line["id"]},
            )
        post_ledger_transaction(
            reference=f"settlement-charge:{item.id}",
            kind="settlement_charge",
            lease=lease,
            invoice=adjustment,
            entries=[
                ("tenant_receivable", "debit", total),
                ("unearned_rent_liability", "credit", total),
            ],
        )
    deposit = DepositAgreement.objects.select_for_update().filter(lease=lease).first()
    if deposit and plan.get("released_deposit_due_minor"):
        deposit.due_minor -= plan["released_deposit_due_minor"]
        deposit.revision += 1
        deposit.save()
    for index, application in enumerate(plan["deposit_applications"]):
        invoice = (
            adjustment
            if application["invoice_id"] == "settlement_invoice"
            else RentInvoice.objects.select_for_update().get(
                id=application["invoice_id"], lease=lease
            )
        )
        amount = application["amount_minor"]
        if (
            not deposit
            or amount
            > deposit.collected_minor - deposit.returned_minor - deposit.applied_minor
            or amount > invoice_balance_minor(invoice)
        ):
            raise RentalConflict(
                "The agreed deposit allocation is no longer available."
            )
        invoice.applied_minor += amount
        invoice.status = (
            "paid" if invoice_balance_minor(invoice) == 0 else "partially_paid"
        )
        invoice.revision += 1
        invoice.save()
        deposit.applied_minor += amount
        deposit.revision += 1
        deposit.save()
        # Deposit is already held cash. Only the approved charge becomes income.
        commission = (
            amount // 10
            if invoice.billing_period and invoice.billing_period.sequence == 1
            else 0
        )
        entries = [
            ("deposit_liability", "debit", amount),
            ("tenant_receivable", "credit", amount),
            ("unearned_rent_liability", "debit", amount),
            ("owner_liability", "credit", amount - commission),
        ]
        if commission:
            entries.append(("commission_reserve", "credit", commission))
        post_ledger_transaction(
            reference=f"settlement-deposit:{item.id}:{index}",
            kind="deposit_applied",
            lease=lease,
            invoice=invoice,
            entries=entries,
        )
        source_settled = (
            not PaymentAttempt.objects.filter(
                invoice=deposit.invoice, payment_status="captured"
            )
            .exclude(settlement_status="settled")
            .exists()
        )
        OwnerPayable.objects.create(
            lease=lease,
            invoice=invoice,
            billing_period=invoice.billing_period,
            source_reference=f"settlement:{item.id}:{index}",
            gross_minor=amount,
            net_minor=amount - commission,
            commission_minor=commission,
            settlement_status="settled" if source_settled else "pending",
        )
    for index, allocation in enumerate(plan["refunds"]):
        attempt = PaymentAttempt.objects.get(
            id=allocation["payment_attempt_id"], invoice__lease=lease
        )
        RefundRequest.objects.create(
            lease=lease,
            payment_attempt=attempt,
            requester=lease.tenant,
            approved_by=item.proposed_by,
            request_key=uuid.uuid5(item.id, f"settlement-refund:{index}"),
            amount_minor=allocation["amount_minor"],
            allocations=allocation["allocations"],
            refundable_balance_snapshot_minor=sum(
                remaining_components(attempt).values()
            ),
            purpose="settlement",
            reason=f"Both parties accepted settlement {item.id}",
            status="approved",
        )
    item.execution_status = "executed"
    item.executed_at = timezone.now()
    item.execution_plan = {
        **plan,
        "adjustment_invoice_id": str(adjustment.id) if adjustment else None,
    }
    item.save(
        update_fields=[
            "execution_status",
            "executed_at",
            "execution_plan",
            "updated_at",
        ]
    )
    from ..rental_phase4_views import evaluate_owner_payables

    evaluate_owner_payables(lease)
    return item
