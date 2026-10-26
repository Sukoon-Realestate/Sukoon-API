"""Narrow financial review; reading an original outcome never submits a refund."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from core_apps.users.models import User
from core_apps.users.services import sensitive_actions, totp
from .models import RefundRequest, PaymobRefund
from .pagination import FeaturePagination
from .renderers import FeatureJsonRenderer
from .services import paymob_client, paymob_refunds
from .services.commands import command_identity
from .services.financial_authority import require_financial_actor, authorization_context
from .services.rental_lifecycle.common import staff_role
from .services.rental_lifecycle.locks import lock_financial_lease
from .services.rental_phase2 import RentalConflict, replay_operation, remember_mutation
from .rental_phase6_views_parts.final_settlement_respond import refund_payload


def reader(user):
    current = User.objects.get(pk=user.pk)
    if not staff_role(current, paymob_refunds.ROLES | {"psp_reconciliation"}):
        raise PermissionDenied("A current refund or reconciliation role is required.")
    return current


def details(refund):
    return {
        "amount_minor": refund.amount_minor,
        "payment_attempt_id": str(refund.payment_attempt.id),
        "allocations": refund.allocations,
        "currency": refund.payment_attempt.currency,
    }


def projection(refund, user):
    item = PaymobRefund.objects.filter(refund=refund, current=True).first()
    can_manage = staff_role(user, paymob_refunds.ROLES)
    restricted = user.sensitive_actions_frozen or totp.pending_recovery(user)
    supported = hasattr(refund.payment_attempt, "paymob_payment")
    can_execute = (
        can_manage and refund.status == "approved" and item is None and supported
    )
    can_reauthorize = (
        can_manage
        and item is not None
        and item.status == "held"
        and item.failure_code == "authorization_changed"
        and item.submitted_at is None
    )
    can_retry = (
        can_manage
        and refund.status == "failed"
        and refund.failure_code == "provider_declined"
        and item is not None
        and item.status == "failed"
        and item.resolved_at is not None
        and item.result_snapshot.get("success") is False
        and item.result_snapshot.get("pending") is False
    )
    actions = []
    reasons = []
    if item and item.status in {
        "submitting",
        "processing",
        "unknown",
        "confirmed",
        "failed",
    }:
        actions.append("reconcile")
    if restricted:
        reasons.append(
            "راجع أمان الحساب قبل إجراء حساس جديد؛ متابعة النتيجة السابقة متاحة."
        )
    elif not paymob_client.refund_ready():
        reasons.append("يحتاج إرسال الاسترداد إلى تجهيز حساب الاختبار الحالي.")
    else:
        if can_execute:
            actions.append("execute")
        if can_reauthorize:
            actions.append("reauthorize")
        if can_retry:
            actions.append("retry")
    if can_manage and refund.status == "requested" and not restricted:
        actions.extend(["approve", "reject"])
    return {
        "resource": refund_payload(refund),
        "instruction_status": item.status if item else None,
        "instruction_id": str(item.id) if item else None,
        "provider_reference": item.provider_transaction_id if item else None,
        "submitted_at": (
            item.submitted_at.isoformat() if item and item.submitted_at else None
        ),
        "can_execute": can_execute,
        "can_reauthorize": can_reauthorize,
        "can_retry": can_retry,
        "allowed_actions": actions,
        "blocking_reasons": reasons,
        "authorization_details": details(refund),
    }


def private(data):
    response = Response(data)
    response["Cache-Control"] = "private, no-store"
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def queue(request):
    current = reader(request.user)
    paginator = FeaturePagination()
    rows = RefundRequest.objects.select_related(
        "lease", "payment_attempt__invoice"
    ).order_by("-created_at", "-pk")
    page = paginator.paginate_queryset(rows, request)
    response = paginator.get_paginated_response(
        [projection(row, current) for row in page]
    )
    response["Cache-Control"] = "private, no-store"
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def review(request, refund_id):
    current = reader(request.user)
    refund = get_object_or_404(
        RefundRequest.objects.select_related("lease", "payment_attempt__invoice"),
        id=refund_id,
    )
    return private(projection(refund, current))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def reconcile(request, refund_id):
    reader(request.user)
    item = get_object_or_404(PaymobRefund, refund__id=refund_id, current=True)
    if request.data.get("provider_transaction_id"):
        paymob_refunds.verify_result(
            item, candidate_id=request.data["provider_transaction_id"]
        )
    else:
        paymob_refunds.process(item, allow_submit=False)
    current = reader(request.user)
    return private(projection(RefundRequest.objects.get(pk=item.refund_id), current))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def retry(request, refund_id):
    key, revision = command_identity(request.data, minimum=1)
    operation = f"refund.retry.{refund_id}"
    # Check replay before any external inquiry, including recovery of a lost reply.
    with transaction.atomic():
        actor = require_financial_actor(
            request.user, paymob_refunds.ROLES, operation, lock=True
        )
        replay = replay_operation(actor, operation, key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
    candidate = get_object_or_404(
        PaymobRefund.objects.select_related("refund__lease", "payment"),
        refund__id=refund_id,
        current=True,
    )
    if (
        str(candidate.id) != request.data.get("failed_instruction_id")
        or candidate.status != "failed"
        or candidate.refund.revision != revision
    ):
        # Another copy of this command may have finished after the first replay
        # check, before the current instruction was read.
        with transaction.atomic():
            actor = require_financial_actor(
                request.user, paymob_refunds.ROLES, operation, lock=True
            )
            replay = replay_operation(actor, operation, key, request.data)
            if replay:
                return Response(replay[0], status=replay[1])
        raise RentalConflict(
            "Refresh the failed attempt before retrying.", code="stale_revision"
        )
    if not paymob_client.refund_ready():
        raise paymob_client.PaymobUnavailable()
    # A fresh authenticated inquiry must still confirm the predecessor's failure.
    paymob_refunds.verify_result(candidate)
    with transaction.atomic():
        actor = require_financial_actor(
            request.user, paymob_refunds.ROLES, operation, lock=True
        )
        replay = replay_operation(actor, operation, key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        lock_financial_lease(candidate.refund.lease)
        refund = RefundRequest.objects.select_for_update().get(pk=candidate.refund_id)
        item = PaymobRefund.objects.select_for_update().get(pk=candidate.pk)
        if refund.revision != revision or not item.current:
            raise RentalConflict("Refresh the original refund.", code="stale_revision")
        if (
            refund.status != "failed"
            or refund.failure_code != "provider_declined"
            or item.status != "failed"
            or item.resolved_at is None
            or item.result_snapshot.get("success") is not False
            or item.result_snapshot.get("pending") is not False
        ):
            raise RentalConflict(
                "Reconcile the original outcome before retrying.",
                code="reconciliation_required",
            )
        if (
            refund.payment_attempt_id != item.payment.attempt_id
            or refund.amount_minor != item.amount_minor
            or refund.allocations != item.allocations
        ):
            raise RentalConflict("The refund details changed.", code="invoice_changed")
        from .services.chargebacks.funding import can_refund
        from .services.refunds import validate_allocations

        if not can_refund(refund.payment_attempt):
            raise RentalConflict(
                "The original funding requires reconciliation.",
                code="payment_not_captured",
            )
        split = validate_allocations(
            refund.payment_attempt,
            item.amount_minor,
            item.allocations,
            exclude_refund=refund,
        )
        sensitive_actions.consume(
            request,
            action="refund.execute",
            resource_id=refund.id,
            revision=refund.revision,
            payload={
                "command": request.data,
                "approval_kind": "retry",
                **details(refund),
            },
        )
        item.current = False
        item.save(update_fields=["current", "updated_at"])
        paymob_refunds.stage(
            refund, refund.payment_attempt, split, actor=actor, retry_of=item
        )
        return Response(
            remember_mutation(
                user=actor,
                operation=operation,
                request_key=key,
                payload=request.data,
                request_subject_id=refund.id,
                result_subject_id=refund.id,
                result_revision=refund.revision,
                resource=refund_payload(refund),
            )
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def reauthorize(request, refund_id):
    key, revision = command_identity(request.data, minimum=1)
    operation = f"refund.reauthorize.{refund_id}"
    with transaction.atomic():
        actor = require_financial_actor(
            request.user, paymob_refunds.ROLES, operation, lock=True
        )
        replay = replay_operation(actor, operation, key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        candidate = get_object_or_404(
            PaymobRefund.objects.select_related("refund__lease"),
            refund__id=refund_id,
            current=True,
        )
        lock_financial_lease(candidate.refund.lease)
        refund = RefundRequest.objects.select_for_update().get(pk=candidate.refund_id)
        item = PaymobRefund.objects.select_for_update().get(pk=candidate.pk)
        if refund.revision != revision:
            raise RentalConflict("Refresh the original refund.", code="stale_revision")
        if (
            item.status != "held"
            or item.failure_code != "authorization_changed"
            or item.submitted_at is not None
            or refund.status != "processing"
        ):
            raise RentalConflict(
                "An unknown refund cannot be submitted again.",
                code="reconciliation_required",
            )
        if not paymob_client.refund_ready():
            raise paymob_client.PaymobUnavailable()
        if (
            refund.amount_minor != item.amount_minor
            or refund.allocations != item.allocations
        ):
            raise RentalConflict("The refund details changed.", code="invoice_changed")
        sensitive_actions.consume(
            request,
            action="refund.execute",
            resource_id=refund.id,
            revision=refund.revision,
            payload={
                "command": request.data,
                "approval_kind": "reauthorize",
                **details(refund),
            },
        )
        item.authorization_context = authorization_context(actor)
        item.status, item.failure_code = "queued", ""
        item.save(
            update_fields=[
                "authorization_context",
                "status",
                "failure_code",
                "updated_at",
            ]
        )
        refund.failure_code = ""
        refund.revision += 1
        refund.save(update_fields=["failure_code", "revision", "updated_at"])
        from .services.refund_notifications import record

        record(refund, "reauthorized", actor)
        return Response(
            remember_mutation(
                user=actor,
                operation=operation,
                request_key=key,
                payload=request.data,
                request_subject_id=refund.id,
                result_subject_id=refund.id,
                result_revision=refund.revision,
                resource=refund_payload(refund),
            )
        )
