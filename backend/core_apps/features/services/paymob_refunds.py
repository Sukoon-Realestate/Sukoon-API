"""Approved refunds reserve money before dispatch; unknown results never resubmit."""

import re
from django.db import transaction, connection
from django.db.models import Sum
from ..models import PaymobPayment, PaymobRefund, RefundRequest
from . import paymob_client as client
from .rental_phase2 import RentalConflict
from .rental_lifecycle.locks import lock_financial_lease


def stage(refund, attempt, allocations):
    """Called by canonical refund execution while holding its financial root."""
    payment = PaymobPayment.objects.get(attempt=attempt)
    existing = PaymobRefund.objects.filter(refund=refund).first()
    if existing:
        return existing
    if not payment.transaction_id or attempt.payment_status != "captured":
        raise RentalConflict(
            "The original Paymob capture is unconfirmed.", code="payment_not_captured"
        )
    if (
        PaymobRefund.objects.filter(payment=payment)
        .exclude(status="confirmed")
        .exists()
    ):
        raise RentalConflict(
            "Resolve the original Paymob refund first.", code="refund_pending"
        )
    previous = (
        RefundRequest.objects.filter(
            payment_attempt=attempt, status="succeeded"
        ).aggregate(total=Sum("amount_minor"))["total"]
        or 0
    )
    item = PaymobRefund.objects.create(
        refund=refund,
        payment=payment,
        amount_minor=refund.amount_minor,
        currency=attempt.currency,
        allocations=allocations,
        refunded_before_minor=previous,
    )
    refund.status, refund.allocations = "processing", allocations
    refund.revision += 1
    refund.save(update_fields=["status", "allocations", "revision", "updated_at"])
    return item


@transaction.atomic
def claim(identity):
    candidate = PaymobRefund.objects.select_related("refund__lease").get(pk=identity)
    lock_financial_lease(candidate.refund.lease)
    refund = RefundRequest.objects.select_for_update().get(pk=candidate.refund_id)
    item = (
        PaymobRefund.objects.select_for_update()
        .select_related("payment__attempt")
        .get(pk=identity)
    )
    if item.status != "queued":
        return None
    if (
        refund.status != "processing"
        or refund.amount_minor != item.amount_minor
        or refund.allocations != item.allocations
    ):
        raise RentalConflict("The approved refund changed.", code="invoice_changed")
    if refund.payment_attempt.invoice.owner_payables.filter(
        payout_status__in=["submitted", "processing"]
    ).exists():
        raise RentalConflict(
            "Reconcile the in-flight payout before refunding.", code="payout_pending"
        )
    item.status = "submitting"
    item.save(update_fields=["status", "updated_at"])
    return item


def process(item):
    if connection.in_atomic_block:
        raise client.PaymobUnavailable()
    item = PaymobRefund.objects.select_related("payment__attempt", "refund__lease").get(
        pk=item.pk
    )
    if item.status == "confirmed":
        return finish_accounting(item)
    if item.status == "queued":
        if not client.refund_ready():
            raise client.PaymobUnavailable()
        source = client.inquiry(item.payment, item.payment.transaction_id)
        order = source.get("order") or {}
        if (
            str(source.get("id")) != item.payment.transaction_id
            or str(order.get("id")) != item.payment.order_id
            or order.get("merchant_order_id") != item.payment.reference
            or source.get("is_live") is not False
            or str(source.get("integration_id")) != item.payment.integration_id
            or source.get("currency") != item.currency
            or type(source.get("amount_cents")) is not int
            or source["amount_cents"] != item.payment.attempt.amount_minor
            or source.get("is_voided") is not False
            or source.get("error_occured") is not False
            or source.get("success") is not True
            or source.get("pending") is not False
            or type(source.get("refunded_amount_cents")) is not int
            or source["refunded_amount_cents"] != item.refunded_before_minor
        ):
            review(item, "refund_balance_mismatch")
            raise RentalConflict(
                "The provider refund balance needs reconciliation.",
                code="outcome_unknown",
            )
        claimed = claim(item.pk)
        if claimed is None:
            return item.refund
        try:
            response = client.submit_refund(item.payment, item.amount_minor)
            identity = str(response.get("id", ""))
            if not re.fullmatch(r"[0-9]{1,18}", identity):
                raise client.PaymobUnavailable()
            PaymobRefund.objects.filter(pk=item.pk).update(
                provider_transaction_id=identity, status="processing"
            )
            item.provider_transaction_id = identity
        except Exception:
            PaymobRefund.objects.filter(pk=item.pk).update(
                status="unknown", failure_code="outcome_unknown"
            )
            review(item, "outcome_unknown")
            raise client.PaymobUnavailable() from None
    if not item.provider_transaction_id:
        # This may have crashed before/after submission. No second POST is safe.
        review(item, "outcome_unknown")
        return item.refund
    return verify_result(item)


def verify_result(item):
    proof = client.inquiry(item.payment, item.provider_transaction_id)
    order = proof.get("order") or {}
    if (
        str(proof.get("id")) != item.provider_transaction_id
        or str(proof.get("parent_transaction")) != item.payment.transaction_id
        or str(order.get("id")) != item.payment.order_id
        or str(proof.get("integration_id")) != item.payment.integration_id
        or proof.get("is_live") is not False
        or proof.get("currency") != item.currency
        or type(proof.get("amount_cents")) is not int
        or proof["amount_cents"] != item.amount_minor
        or proof.get("is_refund") is not True
    ):
        review(item, "refund_identity_mismatch")
        raise RentalConflict(
            "The provider refund identity does not match.",
            code="provider_payment_mismatch",
        )
    if (
        proof.get("success") is not True
        or proof.get("pending") is not False
        or proof.get("error_occured") is not False
    ):
        return item.refund
    PaymobRefund.objects.filter(pk=item.pk).update(status="confirmed", failure_code="")
    return finish_accounting(item)


def finish_accounting(item):
    from .refunds import execute_refund

    # Confirmed proof is committed before accounting, so a DB/domain failure
    # can be repaired without repeating the provider refund.
    return execute_refund(RefundRequest.objects.get(pk=item.refund_id))


def confirmed_reference(refund, payload):
    item = (
        PaymobRefund.objects.select_related("payment")
        .filter(refund=refund, status="confirmed")
        .first()
    )
    if (
        not item
        or not item.provider_transaction_id
        or item.amount_minor != payload["amount_minor"]
        or item.currency != payload["currency"]
        or item.allocations != payload["allocations"]
    ):
        raise RentalConflict(
            "Verified provider refund execution is required.",
            code="provider_execution_required",
        )
    return item.provider_transaction_id


def review(item, code):
    from .rental_lifecycle.cases import open_system_case

    PaymobRefund.objects.filter(pk=item.pk).update(failure_code=code)
    open_system_case(
        kind="refund_failure",
        source_key=f"paymob-refund:{item.id}",
        lease=item.refund.lease,
        attempt=item.payment.attempt,
        reason="A Paymob refund needs reconciliation.",
        next_action="Verify the original refund transaction. Never submit another refund while the outcome is unknown.",
    )
