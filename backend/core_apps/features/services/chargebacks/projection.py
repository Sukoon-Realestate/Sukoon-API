from django.db.models import Sum, Q
from ...models import RentalChargeback, RefundRequest


def totals(item):
    restored = item.restorations.aggregate(
        received=Sum("amount_minor"),
        applied=Sum("invoice_applied_minor"),
        overlap=Sum("overlap_restored_minor"),
        excess=Sum("excess_minor"),
    )
    value = {key: amount or 0 for key, amount in restored.items()}
    replacements = list(item.replacement_payments.select_related("payment_attempt"))
    value["replacement_captured"] = sum(
        row.amount_minor
        for row in replacements
        if row.payment_attempt.payment_status == "captured"
    )
    value["replacement_settled"] = sum(
        row.amount_minor
        for row in replacements
        if row.payment_attempt.payment_status == "captured"
        and row.payment_attempt.settlement_status == "settled"
    )
    value["excess_returned"] = sum(
        row.excess_minor
        for row in item.restorations.select_related("excess_refund")
        if row.excess_refund_id and row.excess_refund.status == "succeeded"
    )
    value["excess"] += sum(row.excess_minor for row in replacements)
    value["excess_returned"] += sum(
        row.excess_minor
        for row in replacements
        if row.excess_refund_id and row.excess_refund.status == "succeeded"
    )
    value["replacement_refunded"] = sum(
        row.amount_minor
        for row in RefundRequest.objects.filter(
            payment_attempt__chargeback_replacement__chargeback=item,
            status="succeeded",
        ).exclude(purpose="chargeback_excess")
    )
    value["allocation_released"] = sum(
        row.amount_minor
        for row in RefundRequest.objects.filter(
            Q(payment_attempt=item.payment_attempt)
            | Q(payment_attempt__chargeback_replacement__chargeback=item),
            status="succeeded",
        )
        .exclude(purpose="chargeback_excess")
        .exclude(id__in=item.source_snapshot.get("prior_refund_ids", []))
    )
    value["retained_funding"] = max(
        value["applied"] + value["replacement_settled"] - value["allocation_released"],
        0,
    )
    value["required_funding"] = max(
        item.invoice_reopened_minor - value["allocation_released"], 0
    )
    return value


def blockers(item):
    value = totals(item)
    reasons = []
    if item.payment_attempt.settlement_status != "settled":
        reasons.append(
            "The original capture settlement still requires provider reconciliation."
        )
    if item.outcome == "open":
        reasons.append("The provider has not supplied a final chargeback decision.")
    if item.outcome in {"won", "reversed"} and value["received"] < item.amount_minor:
        reasons.append(
            "The final decision is not evidence that the disputed funds were restored."
        )
    if value["overlap"] < item.prior_refund_overlap_minor:
        reasons.append(
            "The provider debit overlaps an earlier refund and still requires actual restoration."
        )
    if value["retained_funding"] < value["required_funding"]:
        reasons.append(
            "The original chargeback funding remains outstanding or unsettled."
        )
    if value["excess"] > value["excess_returned"]:
        reasons.append(
            "Restored funds exceeded the remaining invoice; the excess refund is still outstanding."
        )
    return reasons


def payload(item):
    value = totals(item)
    reasons = blockers(item)
    return {
        "id": str(item.id),
        "revision": item.revision,
        "resolved": bool(item.resolved_at and not reasons),
        "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
        "payment_attempt_id": str(item.payment_attempt.id),
        "provider_outcome": item.outcome,
        "amount_minor": item.amount_minor,
        "currency": item.currency,
        "exponent": item.exponent,
        "invoice_reopened_minor": item.invoice_reopened_minor,
        "funds_restored_minor": value["received"],
        "replacement_captured_minor": value["replacement_captured"],
        "replacement_settled_minor": value["replacement_settled"],
        "retained_original_funding_minor": value["retained_funding"],
        "remaining_funding_minor": max(
            value["required_funding"] - value["retained_funding"], 0
        ),
        "original_allocation_released_by_refund_minor": value["allocation_released"],
        "excess_refund_remaining_minor": value["excess"] - value["excess_returned"],
        "blocking_reasons": reasons,
        "excess_refunds": [
            {
                "id": str(row.excess_refund.id),
                "status": row.excess_refund.status,
                "amount_minor": row.excess_minor,
            }
            for row in item.restorations.select_related("excess_refund")
            if row.excess_refund_id
        ]
        + [
            {
                "id": str(row.excess_refund.id),
                "status": row.excess_refund.status,
                "amount_minor": row.excess_minor,
            }
            for row in item.replacement_payments.select_related("excess_refund")
            if row.excess_refund_id
        ],
    }


def lease_blockers(lease):
    reasons = []
    for attempt in lease.invoices.filter(
        payment_attempts__payment_status="chargedback"
    ).values_list("payment_attempts__pk", flat=True):
        item = RentalChargeback.objects.filter(payment_attempt_id=attempt).first()
        if item is None:
            reasons.append(
                "A historical chargeback requires its original provider evidence before reconciliation."
            )
        else:
            reasons.extend(blockers(item))
    return list(dict.fromkeys(reasons))


def funding_ready(attempt):
    if attempt.payment_status == "captured":
        return attempt.settlement_status == "settled"
    if attempt.payment_status != "chargedback":
        return False
    item = RentalChargeback.objects.filter(payment_attempt=attempt).first()
    return bool(item and not blockers(item) and totals(item)["retained_funding"] > 0)


def payable_funding_sources(payable):
    """Resolve current cash sources without changing historical payout facts.

    Settlement deposit applications create a new receivable allocation, not a
    new provider capture. Their payable still depends on the original deposit
    invoice's cash; a null payment_attempt must never bypass that dependency.
    Callers hold the canonical company/property/lease financial locks.
    """
    if payable.payment_attempt_id:
        return [payable.payment_attempt]
    if not payable.source_reference.startswith("settlement:"):
        return []
    from ...models import DepositAgreement, PaymentAttempt

    deposit = DepositAgreement.objects.filter(lease_id=payable.lease_id).first()
    if not deposit or not deposit.invoice_id or not deposit.collected_minor:
        return []
    return list(
        PaymentAttempt.objects.filter(
            invoice_id=deposit.invoice_id,
            payment_status__in=["captured", "chargedback"],
        ).order_by("pk")
    )


def payable_funding_ready(payable):
    sources = payable_funding_sources(payable)
    return bool(sources and all(funding_ready(attempt) for attempt in sources))
