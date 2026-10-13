"""Rental phase6 views: refund execute."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from ..models import (
    DepositAgreement,
    FinalSettlement,
    Lease,
    MaintenanceRequest,
    RefundRequest,
    RentalChange,
    RentalDispute,
    RentalHandover,
    RentalPayout,
    RentInvoice,
)
from ..providers import fake_provider_available
from ..renderers import FeatureJsonRenderer
from ..services.cycle_permissions import cycle_actions
from ..services.commands import command_identity, money_minor
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from ..services.rental_phase6 import evaluate_financial_closure
from .final_settlement_respond import refund_payload, _refund


SUBJECT_MODELS = {
    "invoice": RentInvoice,
    "deposit": DepositAgreement,
    "handover": RentalHandover,
    "maintenance": MaintenanceRequest,
    "change": RentalChange,
    "payout": RentalPayout,
    "refund": RefundRequest,
    "settlement": FinalSettlement,
}


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def refund_execute(request, refund_id):
    """Operations command; the worker calls the same idempotent service."""
    from ..services.refunds import execute_refund
    from ..services.rental_phase3 import post_ledger_transaction

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
        raise PermissionDenied("A financial operations role is required.")
    key, revision = command_identity(request.data, minimum=1)
    recover = request.data.get("action") == "confirm_owner_recovery"
    if request.data.get("action", "execute") not in {
        "execute",
        "confirm_owner_recovery",
    }:
        raise ValidationError({"action": "Use execute or confirm_owner_recovery."})
    if recover and not fake_provider_available():
        raise NotFound()
    operation = f"refund.{'recover' if recover else 'execute'}.{item.id}"
    with transaction.atomic():
        lease = Lease.objects.select_for_update().get(pk=item.lease_id)
        item = RefundRequest.objects.select_for_update().get(pk=item.pk)
        replay = replay_operation(request.user, operation, key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        if item.revision != revision:
            raise RentalConflict("Refund revision conflict.", code="stale_revision")
        if recover:
            outstanding = item.owner_recovery_minor - item.owner_recovered_minor
            if item.status != "succeeded" or outstanding <= 0:
                raise RentalConflict("No owner recovery is outstanding.")
            if money_minor(request.data.get("amount")) != outstanding:
                raise ValidationError(
                    {"amount": "Confirm the exact outstanding owner recovery."}
                )
            post_ledger_transaction(
                reference=f"owner-recovered:{item.id}",
                kind="owner_recovery",
                lease=lease,
                entries=[
                    ("platform_cash", "debit", outstanding),
                    ("owner_receivable", "credit", outstanding),
                ],
                metadata={"provider_mode": "mock", "actor_id": str(request.user.id)},
            )
            item.owner_recovered_minor += outstanding
            item.recovery_reference = f"mock-recovery:{key}"
            item.revision += 1
            item.save()
        else:
            if item.status != "approved":
                raise RentalConflict("Only an approved refund can execute.")
            item = execute_refund(item)
        evaluate_financial_closure(lease)
        return Response(
            remember_mutation(
                user=request.user,
                operation=operation,
                request_key=key,
                payload=request.data,
                request_subject_id=item.id,
                result_subject_id=item.id,
                result_revision=item.revision,
                resource=refund_payload(item),
            )
        )


def dispute_payload(item, user=None):
    return {
        "allowed_actions": cycle_actions(user, item),
        "blocking_reasons": [],
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "subject_kind": item.subject_kind,
        "subject_id": str(item.subject_id),
        "revision": item.revision,
        "status": item.status,
        "reason": item.reason,
        "resolution": item.resolution,
        "responses": item.responses,
        "evidence": [
            {"id": str(x.id), "sha256": x.sha256, "status": "ready"}
            for x in item.evidence.all()
        ],
    }


def _dispute(request, dispute_id, allow_operations=False, lock=False):
    queryset = RentalDispute.objects.select_related(
        "lease__owner", "lease__tenant"
    ).prefetch_related("evidence")
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    item = get_object_or_404(queryset, id=dispute_id)
    profile = getattr(request.user, "staff_profile", None)
    operator = allow_operations and (
        request.user.is_superuser
        or (
            profile
            and profile.is_active
            and profile.role_name == StaffProfile.RoleName.DISPUTE_RESOLVER
        )
    )
    if request.user not in (item.lease.owner, item.lease.tenant) and not operator:
        raise NotFound()
    return item
