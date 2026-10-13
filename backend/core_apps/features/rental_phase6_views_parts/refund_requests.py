"""Rental phase6 views: refund requests."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from ..models import Lease, PaymentAttempt, RefundRequest
from ..renderers import FeatureJsonRenderer
from ..services.commands import command_identity, money_minor
from ..services.refunds import validate_allocations
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from ..services.rental_phase6 import refundable_balance_minor
from .final_settlement_propose import _lease
from .final_settlement_respond import refund_payload, _refund


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def refund_requests(request):
    if request.method == "GET":
        workspace = request.query_params.get("workspace")
        queryset = (
            RefundRequest.objects.filter(lease__owner=request.user)
            if workspace == "owner"
            else RefundRequest.objects.filter(lease__tenant=request.user)
        )
        if request.query_params.get("lease_id"):
            queryset = queryset.filter(lease__id=request.query_params["lease_id"])
        results = [
            refund_payload(x)
            for x in queryset.select_related("lease", "payment_attempt__invoice")
        ]
        return Response(
            {"count": len(results), "next": None, "previous": None, "results": results}
        )
    attempt = get_object_or_404(
        PaymentAttempt.objects.select_related("invoice__lease"),
        id=request.data.get("payment_attempt_id"),
    )
    lease = _lease(request, attempt.invoice.lease.id)
    if request.user != attempt.payer:
        raise PermissionDenied("Only the captured payer can request a refund.")
    request_key, expected_revision = command_identity(request.data)
    if expected_revision != 0:
        raise ValidationError(
            {"expected_revision": "A new refund starts at revision 0."}
        )
    if request.data.get("lease_id") and str(request.data["lease_id"]) != str(lease.id):
        raise ValidationError({"lease_id": "Payment belongs to a different lease."})
    operation = f"refund.create.{attempt.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    amount = money_minor(request.data.get("amount"))
    if (
        not isinstance(amount, int)
        or amount <= 0
        or amount > refundable_balance_minor(attempt)
    ):
        raise RentalConflict(
            "Refund exceeds the remaining refundable capture balance.",
            code="refund_exceeds_balance",
        )
    with transaction.atomic():
        lease = _lease(request, lease.id, lock=True)
        attempt = PaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        if amount > refundable_balance_minor(attempt):
            raise RentalConflict(
                "Refund exceeds the remaining refundable capture balance.",
                code="refund_exceeds_balance",
            )
        if attempt.payment_status != "captured":
            raise RentalConflict(
                "Only confirmed captures can be refunded.", code="payment_not_captured"
            )
        if request.data.get("payment_revision", attempt.revision) != attempt.revision:
            raise RentalConflict("Payment revision conflict.", code="stale_revision")
        allocations = validate_allocations(
            attempt, amount, request.data.get("allocations")
        )
        item = RefundRequest.objects.create(
            lease=lease,
            payment_attempt=attempt,
            requester=request.user,
            amount_minor=amount,
            refundable_balance_snapshot_minor=refundable_balance_minor(attempt),
            reason=request.data.get("reason", ""),
            request_key=request_key,
            allocations=allocations,
        )
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=attempt.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=refund_payload(item),
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def refund_detail(request, refund_id):
    return Response(refund_payload(_refund(request, refund_id)))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def refund_respond(request, refund_id):
    item = _refund(request, refund_id, allow_operations=True)
    profile = getattr(request.user, "staff_profile", None)
    if not request.user.is_superuser and (
        not profile
        or not profile.is_active
        or profile.role_name
        not in {
            StaffProfile.RoleName.REFUND_OPERATOR,
            StaffProfile.RoleName.FINANCIAL_APPROVER,
        }
    ):
        raise PermissionDenied("Refund approval requires an operations role.")
    action = request.data.get("action") or request.data.get("decision")
    if action not in {"approve", "reject"}:
        raise ValidationError({"action": "Must be approve or reject."})
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"refund.respond.{item.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        Lease.objects.select_for_update().get(pk=item.lease_id)
        item = _refund(request, refund_id, allow_operations=True, lock=True)
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        if item.revision != int(request.data.get("expected_revision", 0)):
            raise RentalConflict("Refund revision conflict.", code="stale_revision")
        if item.status != RefundRequest.Status.REQUESTED:
            raise RentalConflict("Only a requested refund can be approved or rejected.")
        item.status = (
            RefundRequest.Status.APPROVED
            if action == "approve"
            else RefundRequest.Status.REJECTED
        )
        item.approved_by = request.user
        item.revision += 1
        item.save()
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=refund_payload(item),
        )
    return Response(output)
