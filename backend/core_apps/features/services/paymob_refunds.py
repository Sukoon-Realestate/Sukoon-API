"""Approved refunds reserve money before dispatch; unknown results never resubmit."""

import re
from django.db import transaction, connection
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from core_apps.admin_api.models import StaffProfile
from ..models import PaymobPayment, PaymobRefund, RefundRequest
from . import paymob_client as client
from .rental_phase2 import RentalConflict
from .rental_lifecycle.locks import lock_financial_lease
from .financial_authority import require_financial_actor, authorization_context

ROLES = {
    StaffProfile.RoleName.REFUND_OPERATOR,
    StaffProfile.RoleName.FINANCIAL_APPROVER,
}


def stage(refund, attempt, allocations, *, actor, retry_of=None):
    """Called by canonical refund execution while holding its financial root."""
    payment = PaymobPayment.objects.get(attempt=attempt)
    existing = PaymobRefund.objects.filter(refund=refund, current=True).first()
    if existing:
        return existing
    if not payment.transaction_id or attempt.payment_status != "captured":
        raise RentalConflict(
            "The original Paymob capture is unconfirmed.", code="payment_not_captured"
        )
    if (
        PaymobRefund.objects.filter(payment=payment, current=True)
        .exclude(status__in=["confirmed", "failed"])
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
        authorization_context=authorization_context(actor),
        retry_of=retry_of,
    )
    refund.status, refund.allocations, refund.failure_code = (
        "processing",
        allocations,
        "",
    )
    refund.revision += 1
    refund.save(
        update_fields=[
            "status",
            "allocations",
            "failure_code",
            "revision",
            "updated_at",
        ]
    )
    from .refund_notifications import record

    record(refund, "retried" if retry_of else "authorized", actor)
    return item


@transaction.atomic
def claim(identity):
    candidate = PaymobRefund.objects.select_related("refund__lease").get(pk=identity)
    actor = (
        User.objects.select_for_update()
        .filter(id=candidate.authorization_context.get("actor_id"))
        .first()
    )
    lock_financial_lease(candidate.refund.lease)
    refund = RefundRequest.objects.select_for_update().get(pk=candidate.refund_id)
    item = (
        PaymobRefund.objects.select_for_update()
        .select_related("payment__attempt")
        .get(pk=identity)
    )
    if not item.current or item.status != "queued":
        return None
    try:
        require_financial_actor(actor, ROLES, "refund.dispatch", lock=True)
        if authorization_context(actor) != item.authorization_context:
            raise PermissionDenied()
    except PermissionDenied:
        item.status = "held"
        item.save(update_fields=["status", "updated_at"])
        review(item, "authorization_changed")
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
    from .chargebacks.funding import can_refund
    from .refunds import validate_allocations

    if not can_refund(refund.payment_attempt):
        raise RentalConflict(
            "The original funding requires reconciliation.", code="payment_not_captured"
        )
    validate_allocations(
        refund.payment_attempt,
        item.amount_minor,
        item.allocations,
        exclude_refund=refund,
    )
    item.status, item.submitted_at = "submitting", timezone.now()
    item.save(update_fields=["status", "submitted_at", "updated_at"])
    refund.revision += 1
    refund.save(update_fields=["revision", "updated_at"])
    from .refund_notifications import record

    record(refund, "submitted", actor)
    return item


def process(item, *, allow_submit=True):
    if connection.in_atomic_block:
        raise client.PaymobUnavailable()
    item = PaymobRefund.objects.select_related("payment__attempt", "refund__lease").get(
        pk=item.pk
    )
    if not item.current or item.status == "failed":
        return item.refund
    if item.status == "confirmed":
        return finish_accounting(item)
    if item.status == "held" or (item.status == "queued" and not allow_submit):
        return item.refund
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
            PaymobRefund.objects.filter(pk=item.pk, status="submitting").update(
                provider_transaction_id=identity, status="processing"
            )
            item.provider_transaction_id = identity
        except Exception:
            PaymobRefund.objects.filter(pk=item.pk, status="submitting").update(
                status="unknown", failure_code="outcome_unknown"
            )
            review(item, "outcome_unknown")
            raise client.PaymobUnavailable() from None
    if not item.provider_transaction_id:
        # This may have crashed before/after submission. No second POST is safe.
        review(item, "outcome_unknown")
        return item.refund
    return verify_result(item)


def verify_result(item, *, candidate_id=None):
    identity = candidate_id or item.provider_transaction_id
    if not identity or not re.fullmatch(r"[0-9]{1,18}", str(identity)):
        raise client.PaymobUnavailable()
    proof = client.inquiry(item.payment, identity)
    order = proof.get("order") or {}
    if (
        str(proof.get("id")) != str(identity)
        or str(proof.get("parent_transaction")) != item.payment.transaction_id
        or str(order.get("id")) != item.payment.order_id
        or order.get("merchant_order_id") != item.payment.reference
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
    succeeded = (
        proof.get("success") is True
        and proof.get("pending") is False
        and proof.get("error_occured") is False
    )
    failed = (
        proof.get("success") is False
        and proof.get("pending") is False
        and type(proof.get("error_occured")) is bool
    )
    contradictory = False
    with transaction.atomic():
        lock_financial_lease(item.refund.lease)
        refund = RefundRequest.objects.select_for_update().get(pk=item.refund_id)
        current = PaymobRefund.objects.select_for_update().get(pk=item.pk)
        if current.provider_transaction_id and current.provider_transaction_id != str(
            identity
        ):
            raise RentalConflict(
                "The confirmed provider identity cannot be replaced.",
                code="provider_payment_mismatch",
            )
        if current.status == "failed":
            if not failed:
                # Never send a replacement after a contradictory observation of
                # its predecessor. Keep both proofs for independent review.
                current.result_snapshot = {
                    **current.result_snapshot,
                    "conflicting_observation": {
                        "transaction_id": str(identity),
                        "success": (
                            proof.get("success")
                            if type(proof.get("success")) is bool
                            else None
                        ),
                        "pending": (
                            proof.get("pending")
                            if type(proof.get("pending")) is bool
                            else None
                        ),
                        "error_occured": (
                            proof.get("error_occured")
                            if type(proof.get("error_occured")) is bool
                            else None
                        ),
                    },
                }
                current.save(update_fields=["result_snapshot", "updated_at"])
                replacement = (
                    PaymobRefund.objects.select_for_update()
                    .filter(refund=refund, current=True)
                    .first()
                )
                if replacement and replacement.status == "queued":
                    replacement.status = "held"
                    replacement.save(update_fields=["status", "updated_at"])
                review(replacement or current, "previous_outcome_changed")
                from .rental_lifecycle.cases import open_system_case

                open_system_case(
                    kind="refund_failure",
                    source_key=f"paymob-refund:{current.id}:contradiction",
                    lease=refund.lease,
                    attempt=current.payment.attempt,
                    reason="The provider returned conflicting outcomes for the same refund attempt.",
                    next_action="Reconcile the original attempt and its replacement before any further refund.",
                )
                contradictory = True
            else:
                return refund
        elif not current.current:
            raise RentalConflict(
                "Review the current attempt.", code="reconciliation_required"
            )
        elif current.status == "confirmed":
            pass
        elif current.status not in {"submitting", "unknown", "processing"} or (
            current.provider_transaction_id
            and current.provider_transaction_id != str(identity)
        ):
            raise RentalConflict(
                "Review the original refund.", code="reconciliation_required"
            )
        else:
            if (
                PaymobRefund.objects.filter(provider_transaction_id=str(identity))
                .exclude(pk=item.pk)
                .exists()
            ):
                raise RentalConflict(
                    "This provider refund is already accounted for.",
                    code="provider_payment_mismatch",
                )
            current.provider_transaction_id = str(identity)
            if succeeded:
                current.status, current.failure_code = "confirmed", ""
            elif failed:
                current.status, current.failure_code = "failed", "provider_declined"
                refund.status, refund.failure_code = "failed", "provider_declined"
                refund.revision += 1
                refund.save(
                    update_fields=["status", "failure_code", "revision", "updated_at"]
                )
                from .refund_notifications import record

                record(refund, "failed")
            else:
                current.status = "processing"
            if succeeded or failed:
                current.resolved_at = timezone.now()
                current.result_snapshot = {
                    "transaction_id": str(identity),
                    "parent_transaction_id": item.payment.transaction_id,
                    "amount_minor": item.amount_minor,
                    "currency": item.currency,
                    "success": proof["success"],
                    "pending": proof["pending"],
                    "error_occured": proof["error_occured"],
                }
            current.save(
                update_fields=[
                    "provider_transaction_id",
                    "status",
                    "failure_code",
                    "resolved_at",
                    "result_snapshot",
                    "updated_at",
                ]
            )
        if not contradictory and current.status != "confirmed":
            return current.refund
    if contradictory:
        raise RentalConflict(
            "The previous result changed; reconcile both attempts.",
            code="reconciliation_required",
        )
    return finish_accounting(item)


def finish_accounting(item):
    from .refunds import execute_refund

    # Confirmed proof is committed before accounting, so a DB/domain failure
    # can be repaired without repeating the provider refund.
    try:
        result = execute_refund(RefundRequest.objects.get(pk=item.refund_id))
    except RentalConflict:
        review(item, "accounting_pending")
        raise
    if result.status != "succeeded":
        review(item, "accounting_pending")
    return result


def confirmed_reference(refund, payload):
    item = (
        PaymobRefund.objects.select_related("payment")
        .filter(refund=refund, current=True, status="confirmed")
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


@transaction.atomic
def review(item, code):
    from .rental_lifecycle.cases import open_system_case

    lock_financial_lease(item.refund.lease)
    refund = RefundRequest.objects.select_for_update().get(pk=item.refund_id)
    current = PaymobRefund.objects.select_for_update().get(pk=item.pk)
    if (
        not current.current
        or refund.status == "succeeded"
        or (current.status == "confirmed" and code != "accounting_pending")
    ):
        return
    PaymobRefund.objects.filter(pk=item.pk).update(failure_code=code)
    if refund.failure_code != code:
        refund.failure_code = code
        refund.revision += 1
        refund.save(update_fields=["failure_code", "revision", "updated_at"])
        from .refund_notifications import record

        record(refund, "review")
    open_system_case(
        kind="refund_failure",
        source_key=f"paymob-refund:{item.id}",
        lease=item.refund.lease,
        attempt=item.payment.attempt,
        reason="A Paymob refund needs reconciliation.",
        next_action="Verify the original refund transaction. Never submit another refund while the outcome is unknown.",
    )
