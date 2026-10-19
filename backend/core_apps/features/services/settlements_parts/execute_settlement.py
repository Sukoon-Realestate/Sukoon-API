"""Settlements: execute settlement."""

import uuid
from django.db import transaction
from django.utils import timezone
from ...models import (
    DepositAgreement,
    FinalSettlement,
    InvoiceLine,
    Lease,
    OwnerPayable,
    PaymentAttempt,
    RefundRequest,
    RentInvoice,
)
from ..rental_phase2 import RentalConflict, fingerprint
from ..rental_phase3 import invoice_balance_minor, post_ledger_transaction
from ..refunds import remaining_components
from .financial_snapshot import financial_snapshot
from .apply_credit import _apply_credit


@transaction.atomic
def execute_settlement(item):
    from ..rental_lifecycle.locks import lock_financial_lease

    lease = lock_financial_lease(Lease.objects.get(pk=item.lease_id))
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
            requester=attempt.payer if lease.renter_company_id else lease.tenant,
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
    from ...rental_phase4_views import evaluate_owner_payables

    evaluate_owner_payables(lease)
    return item
