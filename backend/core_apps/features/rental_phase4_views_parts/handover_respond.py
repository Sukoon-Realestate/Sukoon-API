"""Rental phase4 views: handover respond."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import (
    DepositAgreement,
    OwnerPaymentProfile,
    PaymentAttempt,
    RentalHandover,
    RentalPayout,
)
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from ..services.rental_phase3 import post_ledger_transaction
from .handover_payload import _money, _lease, handover_payload, _handover
from .lease_handovers import deposit_payload


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_deposit(request, lease_id):
    lease = _lease(request, lease_id)
    # Issuance belongs to the signing transaction. A read must not create a
    # separate charge, especially after the combined invoice was already paid.
    deposit = get_object_or_404(DepositAgreement, lease=lease)
    return Response(deposit_payload(deposit))


def evaluate_owner_payables(lease):
    profile = OwnerPaymentProfile.objects.filter(owner=lease.owner).first()
    move_in = lease.handovers.filter(
        kind=RentalHandover.Kind.MOVE_IN, status=RentalHandover.Status.ACCEPTED
    ).exists()
    for payable in lease.owner_payables.select_for_update():
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
        if payable.source_reference and payable.settlement_status != "settled":
            deposit = DepositAgreement.objects.filter(lease=lease).first()
            if (
                deposit
                and not PaymentAttempt.objects.filter(
                    invoice=deposit.invoice, payment_status="captured"
                )
                .exclude(settlement_status="settled")
                .exists()
            ):
                payable.settlement_status = "settled"
        reasons = []
        if payable.settlement_status != "settled":
            reasons.append("PSP settlement is pending.")
        if not move_in:
            reasons.append("Move-in is not accepted.")
        if not profile or not profile.payout_ready:
            reasons.append("Owner beneficiary is not ready.")
        if not profile or "rental-policy-v1" not in profile.accepted_policy_versions:
            reasons.append("Required policy is not accepted.")
        if lease.refund_requests.filter(
            status__in=["requested", "approved", "processing"]
        ).exists():
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
            post_ledger_transaction(
                reference=f"commission-earned:{payable.id}",
                kind="commission_earned",
                lease=lease,
                invoice=payable.invoice,
                attempt=payable.payment_attempt,
                entries=[
                    ("commission_reserve", "debit", payable.commission_minor),
                    ("commission_revenue", "credit", payable.commission_minor),
                ],
            )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def handover_respond(request, handover_id):
    action = request.data.get("action") or request.data.get("decision")
    if action not in {"accept", "dispute"} or not request.data.get("request_key"):
        raise ValidationError(
            "accept/dispute, expected_revision, and request_key are required."
        )
    handover = _handover(request, handover_id)
    operation = f"handover.respond.{handover.id}.{request.user.id}"
    replay = replay_operation(
        request.user, operation, request.data["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        handover = _handover(request, handover_id, lock=True)
        if int(request.data.get("expected_revision", 0)) != handover.revision:
            raise RentalConflict("Handover revision conflict.", code="stale_revision")
        if handover.status == RentalHandover.Status.ACCEPTED:
            raise RentalConflict("This handover is already accepted.")
        approvals = set(handover.approvals)
        if action == "dispute":
            handover.status = RentalHandover.Status.DISPUTED
            handover.lease.occupancy_status = "handover_disputed"
        else:
            approvals.add(str(request.user.id))
            handover.approvals = sorted(approvals)
            if {str(handover.lease.owner.id), str(handover.lease.tenant.id)}.issubset(
                approvals
            ):
                handover.status = RentalHandover.Status.ACCEPTED
                handover.accepted_at = timezone.now()
                if handover.kind == RentalHandover.Kind.MOVE_IN:
                    handover.lease.occupancy_status = "occupied"
                else:
                    handover.lease.occupancy_status = "returned"
                    from ..models import RentalInventoryDayLock

                    RentalInventoryDayLock.objects.filter(
                        lease=handover.lease, kind=RentalInventoryDayLock.Kind.OCCUPIED
                    ).delete()
            else:
                handover.status = RentalHandover.Status.PENDING_APPROVAL
        handover.revision += 1
        handover.save()
        if (
            handover.kind == RentalHandover.Kind.MOVE_IN
            and handover.status == RentalHandover.Status.ACCEPTED
        ):
            evaluate_owner_payables(handover.lease)
        handover.lease.revision += 1
        handover.lease.save(
            update_fields=["occupancy_status", "revision", "updated_at"]
        )
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request.data["request_key"],
            payload=request.data,
            request_subject_id=handover.id,
            result_subject_id=handover.id,
            result_revision=handover.revision,
            resource=handover_payload(handover, request.user),
        )
    return Response(output)


def payout_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "status": item.status,
        "amount": _money(item.amount_minor),
        "masked_beneficiary": item.masked_beneficiary,
        "reason": item.hold_reason or item.failure_code,
        "submitted_at": item.created_at.isoformat(),
        "succeeded_at": (
            item.updated_at.isoformat()
            if item.status == RentalPayout.Status.PAID
            else None
        ),
        "payable_ids": [str(x.id) for x in item.payables.all()],
    }
