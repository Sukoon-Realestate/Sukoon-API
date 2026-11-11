"""Owner payable eligibility; callers hold the canonical financial lease lock."""

from ..models import LedgerTransaction, OwnerPaymentProfile, RentalHandover
from .rental_phase3 import post_ledger_transaction


def evaluate_owner_payables(lease):
    move_in = lease.handovers.filter(
        kind=RentalHandover.Kind.MOVE_IN, status=RentalHandover.Status.ACCEPTED
    ).exists()
    pending_refund = lease.refund_requests.filter(
        status__in=["requested", "approved", "processing"]
    ).exists()
    payables = list(
        lease.owner_payables.select_for_update(of=("self",))
        .select_related("invoice", "payment_attempt")
        .order_by("pk")
    )
    profiles = {
        profile.owner_id: profile
        for profile in OwnerPaymentProfile.objects.filter(
            owner_id__in={payable.invoice.beneficiary_id or lease.owner_id for payable in payables}
        )
    }
    for payable in payables:
        profile = profiles.get(payable.invoice.beneficiary_id or lease.owner_id)
        if payable.payout_status in {
            "submitted",
            "processing",
            "succeeded",
            "cancelled",
        }:
            continue
        previous = (
            payable.settlement_status,
            payable.payout_status,
            payable.blocking_reasons,
        )
        from .chargebacks.projection import (
            payable_funding_ready,
            payable_funding_sources,
        )

        funded = payable_funding_ready(payable)
        if funded:
            payable.settlement_status = "settled"
        reasons = []
        if not funded:
            reasons.append(
                "A chargeback of the original cash source requires canonical financial reconciliation."
                if any(
                    attempt.payment_status == "chargedback"
                    for attempt in payable_funding_sources(payable)
                )
                else "The original cash source requires canonical financial reconciliation."
            )
        if payable.settlement_status != "settled":
            reasons.append("PSP settlement is pending.")
        if not move_in:
            reasons.append("Move-in is not accepted.")
        if not profile or not profile.payout_ready:
            reasons.append("Owner beneficiary is not ready.")
        if not profile or "rental-policy-v1" not in profile.accepted_policy_versions:
            reasons.append("Required policy is not accepted.")
        if pending_refund:
            reasons.append("A refund is awaiting resolution.")
        payable.blocking_reasons = reasons
        payable.payout_status = "ready" if not reasons else "held"
        if previous != (
            payable.settlement_status,
            payable.payout_status,
            payable.blocking_reasons,
        ):
            payable.revision += 1
            payable.save()
        if not reasons and payable.commission_minor:
            # Recognition is an immutable historical source. Refunds post their
            # own additive reversal; re-evaluation must not rewrite recognition
            # using the payable's now reduced commission balance.
            reference = f"commission-earned:{payable.id}"
            recognized = LedgerTransaction.objects.filter(reference=reference).first()
            amount = (
                recognized.entries.get(account="commission_reserve", direction="debit").amount_minor
                if recognized
                else payable.commission_minor
            )
            post_ledger_transaction(
                reference=reference,
                kind="commission_earned",
                lease=lease,
                invoice=payable.invoice,
                attempt=payable.payment_attempt,
                entries=[
                    ("commission_reserve", "debit", amount),
                    ("commission_revenue", "credit", amount),
                ],
            )
