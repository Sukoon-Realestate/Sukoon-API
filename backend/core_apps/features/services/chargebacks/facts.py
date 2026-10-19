"""Apply authenticated full-dispute facts while retaining the original allocation."""

from django.db import IntegrityError, transaction
from django.db.models import Sum
from ...models import (
    ChargebackRestoration,
    OwnerPayable,
    RentalChargeback,
    RentInvoice,
)
from ..rental_phase2 import RentalConflict
from ..rental_phase3_parts.issue_invoice import post_ledger_transaction
from .projection import totals


EVENTS = {"payment.chargeback.decided", "payment.chargeback.restored"}


def unique_record(model, **values):
    try:
        with transaction.atomic():
            return model.objects.create(**values)
    except IntegrityError:
        raise RentalConflict(
            "The original provider identity is already bound to another financial fact.",
            code="financial_source_conflict",
        )


def refresh_invoice(invoice):
    from ..rental_phase3_parts.payment_attempt_payload import invoice_balance_minor

    invoice.status = (
        "paid"
        if not invoice_balance_minor(invoice)
        else ("partially_paid" if invoice.applied_minor else "due")
    )
    invoice.revision += 1
    invoice.save()


def changed(item, reason):
    from ..rental_lifecycle.cases import open_system_case
    from ..rental_phase6 import evaluate_financial_closure
    from ..rental_lifecycle.common import audit
    from ...rental_phase4_views_parts.handover_respond import evaluate_owner_payables
    from .projection import blockers
    from django.utils import timezone

    item.resolved_at = (
        (item.resolved_at or timezone.now()) if not blockers(item) else None
    )
    item.revision += 1
    item.save()
    lease = item.payment_attempt.invoice.lease
    open_system_case(
        kind="chargeback",
        source_key=f"chargeback:{item.id}",
        lease=lease,
        attempt=item.payment_attempt,
        actor=item.payment_attempt.payer,
        reason="An authenticated chargeback requires its final decision and canonical financial resolution.",
        next_action=(
            "Inspect the chargeback evidence, reconcile original funding, and approve any exact excess refund. "
            "A case note cannot move money."
        ),
    )
    audit(
        item, None, "chargeback." + reason, metadata={"provider_outcome": item.outcome}
    )
    lease.revision += 1
    lease.save(update_fields=["revision", "updated_at"])
    evaluate_owner_payables(lease)
    evaluate_financial_closure(lease, increment_revision=False)
    if lease.renter_company_id:
        from ..company.tenancy_access import notify

        notify(lease.company_tenancy)
    return item


def open_dispute(attempt, event):
    item = (
        RentalChargeback.objects.select_for_update()
        .filter(payment_attempt=attempt)
        .first()
    )
    identity = str(event.payload.get("dispute_id") or event.provider_event_id)
    if not identity or len(identity) > 120:
        raise RentalConflict("The original provider dispute identity is required.")
    if item:
        if identity != item.provider_dispute_id:
            raise RentalConflict(
                "A second dispute episode requires a separate provider contract.",
                code="chargeback_episode_unsupported",
            )
        if event.provider != item.provider:
            raise RentalConflict(
                "The chargeback provider does not match the original event."
            )
        return item
    if attempt.payment_status == "chargedback":
        raise RentalConflict(
            "Reconcile the historical chargeback using its original evidence before accepting new facts.",
            code="legacy_chargeback_review",
        )
    if hasattr(attempt, "chargeback_replacement"):
        raise RentalConflict(
            "A chargeback of a replacement payment needs a separately supported dispute episode.",
            code="chargeback_episode_unsupported",
        )
    if RentalChargeback.objects.filter(
        provider=event.provider, provider_dispute_id=identity
    ).exists():
        raise RentalConflict(
            "This provider dispute identity already belongs to another payment.",
            code="chargeback_source_mismatch",
        )
    invoice = RentInvoice.objects.select_for_update().get(pk=attempt.invoice_id)
    refunded = (
        attempt.refund_requests.filter(status="succeeded").aggregate(
            total=Sum("amount_minor")
        )["total"]
        or 0
    )
    reopened = min(invoice.applied_minor, max(attempt.amount_minor - refunded, 0))
    payable = (
        OwnerPayable.objects.select_for_update().filter(payment_attempt=attempt).first()
    )
    item = unique_record(
        RentalChargeback,
        payment_attempt=attempt,
        opening_event=event,
        provider=event.provider,
        provider_dispute_id=identity,
        amount_minor=attempt.amount_minor,
        currency=attempt.currency,
        exponent=attempt.exponent,
        invoice_reopened_minor=reopened,
        prior_refund_overlap_minor=attempt.amount_minor - reopened,
        source_snapshot={
            "invoice_revision": invoice.revision,
            "invoice_applied_minor": invoice.applied_minor,
            "invoice_charges_minor": invoice.charges_minor,
            "invoice_credits_minor": invoice.credits_minor,
            "refunded_minor": refunded,
            "settlement_status": attempt.settlement_status,
            "prior_refund_ids": list(
                map(
                    str,
                    attempt.refund_requests.filter(status="succeeded").values_list(
                        "id", flat=True
                    ),
                )
            ),
            "payable_id": str(payable.id) if payable else None,
            "payout_status": payable.payout_status if payable else None,
            "opening_payload_digest": event.payload_digest,
        },
    )
    attempt.payment_status = "chargedback"
    attempt.revision += 1
    attempt.save()
    invoice.applied_minor -= reopened
    refresh_invoice(invoice)
    post_ledger_transaction(
        reference=f"chargeback:{attempt.id}",
        kind="chargeback",
        lease=invoice.lease,
        invoice=invoice,
        attempt=attempt,
        entries=[
            ("chargeback_receivable", "debit", attempt.amount_minor),
            ("platform_cash", "credit", attempt.amount_minor),
        ],
    )
    if reopened:
        # Reopen the already agreed invoice rather than creating a second charge.
        post_ledger_transaction(
            reference=f"chargeback-invoice:{item.id}",
            kind="chargeback_invoice_reopened",
            lease=invoice.lease,
            invoice=invoice,
            attempt=attempt,
            entries=[
                ("tenant_receivable", "debit", reopened),
                ("chargeback_receivable", "credit", reopened),
            ],
        )
    if payable and payable.payout_status not in {
        "submitted",
        "processing",
        "succeeded",
        "cancelled",
    }:
        payable.payout_status = "held"
        payable.blocking_reasons = ["A chargeback is unresolved."]
        payable.revision += 1
        payable.save()
    return changed(item, "opened")


def apply_fact(attempt, event):
    data = event.payload
    original = data.get("chargeback_event_id")
    if not isinstance(original, str) or not original or len(original) > 120:
        raise RentalConflict(
            "The exact original chargeback event identity is required.",
            code="chargeback_source_mismatch",
        )
    if event.event_type == "payment.chargeback.decided" and data.get("outcome") not in {
        "won",
        "lost",
        "reversed",
    }:
        raise RentalConflict("A final provider outcome must be won, lost or reversed.")
    if event.event_type == "payment.chargeback.restored":
        amount, reference = data.get("amount_minor"), data.get("cash_reference")
        if (
            type(amount) is not int
            or not 0 < amount <= attempt.amount_minor
            or data.get("funds_status") != "received"
            or not isinstance(reference, str)
            or not reference.strip()
            or len(reference) > 120
        ):
            raise RentalConflict(
                "Supply a bounded authenticated receipt of restored funds, not only a successful dispute decision.",
                code="chargeback_cash_evidence_required",
            )
    item = (
        RentalChargeback.objects.select_for_update()
        .filter(payment_attempt=attempt)
        .first()
    )
    if item is None:
        return False  # A final result can arrive before the opening event.
    if (
        event.provider != item.provider
        or data.get("chargeback_event_id") != item.opening_event.provider_event_id
        or data.get("dispute_id", item.provider_dispute_id) != item.provider_dispute_id
    ):
        raise RentalConflict(
            "The provider fact must reference this exact original chargeback.",
            code="chargeback_source_mismatch",
        )
    if event.event_type == "payment.chargeback.decided":
        outcome = data.get("outcome")
        if item.outcome != "open":
            if item.outcome != outcome:
                raise RentalConflict(
                    "Conflicting final chargeback outcomes require original provider reconciliation."
                )
            return True
        item.outcome, item.outcome_event = outcome, event
        changed(item, "decision_recorded")
    elif event.event_type == "payment.chargeback.restored":
        restore(item, event)
    return True


def restore(item, event):
    from ..rental_phase3_parts.payment_attempt_payload import invoice_balance_minor
    from .refunds import create_excess_refund

    if ChargebackRestoration.objects.filter(provider_event=event).exists():
        return
    data, value = event.payload, totals(item)
    amount = data.get("amount_minor")
    cash_reference = str(data.get("cash_reference", "")).strip()
    previous = ChargebackRestoration.objects.filter(
        provider=event.provider, cash_reference=cash_reference
    ).first()
    if previous:
        if previous.chargeback_id != item.pk or previous.amount_minor != amount:
            raise RentalConflict(
                "A restored-cash reference cannot be reused for different funding.",
                code="financial_source_conflict",
            )
        return
    if (
        type(amount) is not int
        or amount <= 0
        or amount > item.amount_minor - value["received"]
        or data.get("funds_status") != "received"
        or not cash_reference
        or len(cash_reference) > 120
    ):
        raise RentalConflict(
            "Supply a bounded authenticated receipt of restored funds, not only a successful dispute decision.",
            code="chargeback_cash_evidence_required",
        )
    invoice = RentInvoice.objects.select_for_update().get(
        pk=item.payment_attempt.invoice_id
    )
    overlap = min(amount, item.prior_refund_overlap_minor - value["overlap"])
    available = amount - overlap
    remaining = max(
        item.invoice_reopened_minor - value["applied"] - value["replacement_captured"],
        0,
    )
    applied = min(available, remaining, invoice_balance_minor(invoice))
    excess = available - applied
    row = unique_record(
        ChargebackRestoration,
        chargeback=item,
        provider_event=event,
        amount_minor=amount,
        provider=event.provider,
        cash_reference=cash_reference,
        invoice_applied_minor=applied,
        overlap_restored_minor=overlap,
        excess_minor=excess,
    )
    from .funding import take_components

    row.components = take_components(item, applied)
    row.save(update_fields=["components", "updated_at"])
    entries = [("platform_cash", "debit", amount)]
    entries += [("tenant_receivable", "credit", applied)] if applied else []
    entries += [("chargeback_receivable", "credit", overlap)] if overlap else []
    entries += [("chargeback_excess_liability", "credit", excess)] if excess else []
    post_ledger_transaction(
        reference=f"chargeback-restored:{row.id}",
        kind="chargeback_restored",
        lease=invoice.lease,
        invoice=invoice,
        attempt=item.payment_attempt,
        entries=entries,
        metadata={
            "provider_event_id": str(event.id),
            "cash_reference": data["cash_reference"],
        },
    )
    if applied:
        invoice.applied_minor += applied
        refresh_invoice(invoice)
    if excess:
        row.excess_refund = create_excess_refund(
            item, item.payment_attempt, row.id, excess
        )
        row.save(update_fields=["excess_refund", "updated_at"])
    changed(item, "funds_restored")
