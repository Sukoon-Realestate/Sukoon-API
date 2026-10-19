"""Return only evidenced excess, through the existing funded refund instruction."""

import uuid
from ...models import ChargebackRestoration, ChargebackReplacementPayment, RefundRequest
from ..rental_phase2 import RentalConflict
from ..rental_phase3_parts.issue_invoice import post_ledger_transaction


def create_excess_refund(item, attempt, identity, amount):
    return RefundRequest.objects.create(
        lease=attempt.invoice.lease,
        payment_attempt=attempt,
        requester=attempt.payer,
        amount_minor=amount,
        refundable_balance_snapshot_minor=amount,
        request_key=uuid.uuid5(identity, "chargeback-excess"),
        purpose="chargeback_excess",
        allocations={"excess": amount},
        reason=(
            "Authenticated funds exceeded the remaining original invoice. "
            "Return only this evidenced excess to the original payer."
        ),
    )


def source(refund):
    row = (
        ChargebackRestoration.objects.select_related("chargeback")
        .filter(excess_refund=refund)
        .first()
    )
    if row:
        return row, "platform_cash"
    row = (
        ChargebackReplacementPayment.objects.select_related("chargeback")
        .filter(excess_refund=refund)
        .first()
    )
    if row:
        return row, (
            "platform_cash"
            if refund.payment_attempt.settlement_status == "settled"
            else "psp_clearing"
        )
    raise RentalConflict(
        "No canonical restored-funds record supports this excess refund."
    )


def execute(refund):
    from ..rental_lifecycle.provider_instructions import execute_local_instruction
    from .facts import changed

    row, cash = source(refund)
    if refund.amount_minor != row.excess_minor or refund.allocations != {
        "excess": row.excess_minor
    }:
        raise RentalConflict("The exact evidenced excess cannot be changed.")
    refund.provider_refund_id = execute_local_instruction(
        kind="refund",
        subject=refund,
        request_key=refund.request_key,
        payload={
            "payment_attempt_id": str(refund.payment_attempt.id),
            "amount_minor": refund.amount_minor,
            "currency": refund.payment_attempt.currency,
            "chargeback_id": str(row.chargeback.id),
            "purpose": "chargeback_excess",
        },
    )
    post_ledger_transaction(
        reference=f"refund:{refund.id}",
        kind="refund",
        lease=refund.lease,
        invoice=refund.payment_attempt.invoice,
        attempt=refund.payment_attempt,
        entries=[
            ("chargeback_excess_liability", "debit", refund.amount_minor),
            (cash, "credit", refund.amount_minor),
        ],
        metadata={
            "purpose": "chargeback_excess",
            "provider_refund_id": refund.provider_refund_id,
        },
    )
    refund.status, refund.failure_code = "succeeded", ""
    refund.revision += 1
    refund.save()
    changed(row.chargeback, "excess_returned")
    return refund
