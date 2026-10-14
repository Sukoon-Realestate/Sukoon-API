"""Rental phase6 views: final settlement respond."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from ..models import FinalSettlement, RefundRequest, RentalDocument
from ..renderers import FeatureJsonRenderer
from ..services.commands import command_identity
from ..services.settlements import execute_settlement
from ..services.settlement_notes import remember_note, validated_note
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from ..services.rental_phase6 import (
    evaluate_financial_closure,
    refundable_balance_minor,
)
from .final_settlement_propose import _money, _lease, settlement_payload


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def final_settlement_respond(request, lease_id):
    lease = _lease(request, lease_id)
    request_key, expected_revision = command_identity(request.data, minimum=1)
    action = request.data.get("action") or request.data.get("decision")
    if action not in {"accept", "dispute"} or not request.data.get("request_key"):
        raise ValidationError("accept/dispute and request_key are required.")
    operation = f"settlement.respond.{lease.id}.{request.user.id}"
    replay = replay_operation(
        request.user, operation, request.data["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    note = validated_note(request.data)
    with transaction.atomic():
        lease = _lease(request, lease_id, lock=True)
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        item = FinalSettlement.objects.select_for_update().get(lease=lease)
        if item.revision != expected_revision:
            raise RentalConflict("Settlement revision conflict.", code="stale_revision")
        if item.status != FinalSettlement.Status.PROPOSED:
            raise RentalConflict("This settlement is not awaiting approval.")
        if str(request.user.id) in item.accepted_by and action == "accept":
            raise RentalConflict("You already accepted this revision.")
        current_ids = {line["id"] for line in item.lines}
        if action == "dispute":
            disputed = set(map(str, request.data.get("item_ids", [])))
            if not disputed or not disputed.issubset(current_ids):
                raise ValidationError(
                    {"item_ids": "Choose persisted settlement item IDs."}
                )
            item.disputed_item_ids = sorted(disputed)
            item.status = FinalSettlement.Status.DISPUTED
            item.accepted_by = []
        else:
            accepted = set(item.accepted_by)
            accepted.add(str(request.user.id))
            item.accepted_by = sorted(accepted)
            if {str(lease.owner.id), str(lease.tenant.id)}.issubset(accepted):
                item.status = FinalSettlement.Status.ACCEPTED
        item.revision += 1
        remember_note(item, request.user, action, note, request_key)
        item.save()
        if item.status == FinalSettlement.Status.ACCEPTED:
            item = execute_settlement(item)
            RentalDocument.objects.get_or_create(
                lease=lease,
                document_type=RentalDocument.DocumentType.SETTLEMENT,
                title="Final settlement",
                defaults={"requested_by": request.user},
            )
        evaluate_financial_closure(lease)
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request.data["request_key"],
            payload=request.data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=settlement_payload(item, request.user),
        )
    return Response(output)


def refund_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "payment_attempt_id": str(item.payment_attempt.id),
        "revision": item.revision,
        "status": item.status,
        "amount": _money(item.amount_minor),
        "refundable_balance": _money(refundable_balance_minor(item.payment_attempt)),
        "reason": item.reason,
        "provider_refund_id": item.provider_refund_id,
        "failure_code": item.failure_code,
        "allocations": item.allocations,
        "purpose": item.purpose,
        "owner_recovery": _money(
            item.owner_recovery_minor - item.owner_recovered_minor
        ),
    }


def _refund(request, refund_id, allow_operations=False, lock=False):
    queryset = RefundRequest.objects.select_related(
        "lease__owner", "lease__tenant", "payment_attempt__invoice"
    )
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    item = get_object_or_404(queryset, id=refund_id)
    profile = getattr(request.user, "staff_profile", None)
    operator = allow_operations and (
        request.user.is_superuser
        or (
            profile
            and profile.is_active
            and profile.role_name
            in {
                StaffProfile.RoleName.REFUND_OPERATOR,
                StaffProfile.RoleName.FINANCIAL_APPROVER,
            }
        )
    )
    if request.user not in (item.lease.owner, item.lease.tenant) and not operator:
        raise NotFound()
    return item
