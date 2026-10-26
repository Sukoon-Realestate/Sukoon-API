"""Refunds: execute refund."""

from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.db.models import Sum
from ...models import (
    DepositAgreement,
    Lease,
    LedgerTransaction,
    OwnerPayable,
    PaymentAttempt,
    RefundRequest,
    RentInvoice,
)
from ..rental_phase2 import RentalConflict
from ..rental_phase3 import invoice_balance_minor, post_ledger_transaction
from .remaining_components import captured_components, validate_allocations


@transaction.atomic
def execute_refund(refund, *, actor=None):
    # Shared lease lock orders settlement, refunds, capture and payouts consistently.
    from ..rental_lifecycle.locks import lock_financial_lease

    if actor is not None:
        from ..financial_authority import require_financial_actor
        from ..paymob_refunds import ROLES

        actor = require_financial_actor(actor, ROLES, "refund.execute", lock=True)
    lease = lock_financial_lease(Lease.objects.get(pk=refund.lease_id))
    refund = RefundRequest.objects.select_for_update().get(pk=refund.pk)
    from ...models import PaymobRefund, PaymobPayment

    confirmed_paymob = PaymobRefund.objects.filter(
        refund=refund, current=True, status="confirmed"
    ).exists()
    provider_payment = PaymobPayment.objects.filter(
        attempt_id=refund.payment_attempt_id
    ).exists()
    if provider_payment and not confirmed_paymob and actor is None:
        # Approval of the request is not authorization to send money. A worker
        # may only dispatch an instruction staged by the sensitive command.
        return refund
    if refund.status != RefundRequest.Status.APPROVED and not (
        refund.status == "processing" and confirmed_paymob
    ):
        return refund
    attempt = PaymentAttempt.objects.select_for_update().get(
        pk=refund.payment_attempt_id
    )
    invoice = RentInvoice.objects.select_for_update().get(pk=attempt.invoice_id)
    if refund.purpose == "chargeback_excess":
        from ..chargebacks.refunds import execute

        return execute(refund)
    from ..chargebacks.funding import can_refund, refund_source

    if not can_refund(attempt):
        raise RentalConflict(
            "Only a confirmed capture can be refunded.", code="payment_not_captured"
        )
    split = validate_allocations(
        attempt, refund.amount_minor, refund.allocations, exclude_refund=refund
    )
    original = refund_source(attempt)
    payable = (
        OwnerPayable.objects.select_for_update()
        .filter(payment_attempt=original)
        .first()
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
        from django.db.models import Q

        previous = RefundRequest.objects.filter(
            Q(payment_attempt=original)
            | Q(
                payment_attempt__chargeback_replacement__chargeback__payment_attempt=original
            ),
            status="succeeded",
        ).exclude(purpose="chargeback_excess")
        original_commission = payable.commission_minor
        if payable.payout_status != "succeeded":
            original_commission += (
                previous.aggregate(total=Sum("commission_reversal_minor"))["total"] or 0
            )
        original_rent = captured_components(original)["rent"]
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
    from ..rental_lifecycle.provider_instructions import execute_local_instruction

    if PaymobPayment.objects.filter(attempt=attempt).exists() and not confirmed_paymob:
        from ..paymob_refunds import stage

        stage(refund, attempt, split, actor=actor)
        return refund
    refund.provider_refund_id = execute_local_instruction(
        kind="refund",
        subject=refund,
        request_key=refund.request_key,
        payload={
            "payment_attempt_id": str(attempt.id),
            "amount_minor": refund.amount_minor,
            "currency": attempt.currency,
            "allocations": split,
        },
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
    from ...rental_phase4_views import evaluate_owner_payables
    from ..rental_phase6 import evaluate_financial_closure

    evaluate_owner_payables(lease)
    evaluate_financial_closure(lease)
    chargeback = getattr(original, "chargeback", None)
    if chargeback:
        from ..chargebacks.facts import changed

        changed(chargeback, "ordinary_refund_recorded")
    from ..refund_notifications import record

    record(refund, "succeeded")
    return refund
