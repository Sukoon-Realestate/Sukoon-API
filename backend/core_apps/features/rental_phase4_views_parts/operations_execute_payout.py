"""Rental phase4 views: operations execute payout."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from ..models import (
    Lease,
    OwnerPayable,
    OwnerPaymentProfile,
    PayoutAuditEvent,
    PayoutBatch,
    RentalPayout,
)
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import (
    RentalConflict,
    remember_mutation,
    replay_operation,
    fingerprint,
)
from .handover_respond import evaluate_owner_payables, payout_payload


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payouts(request):
    if request.query_params.get("workspace") != "owner":
        raise ValidationError({"workspace": "Must be owner."})
    queryset = RentalPayout.objects.filter(owner=request.user).prefetch_related(
        "payables"
    )
    if request.query_params.get("lease_id"):
        queryset = queryset.filter(lease__id=request.query_params["lease_id"])
    results = [payout_payload(x) for x in queryset]
    return Response(
        {"count": len(results), "next": None, "previous": None, "results": results}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payout_detail(request, payout_id):
    item = get_object_or_404(
        RentalPayout.objects.prefetch_related("payables"),
        id=payout_id,
        owner=request.user,
    )
    return Response(payout_payload(item))


def _require_payout_role(user, *, lock=False):
    from ..services.financial_authority import require_financial_actor

    return require_financial_actor(
        user, {StaffProfile.RoleName.PAYOUT_OPERATOR}, "payout.execute", lock=lock
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def operations_execute_payout(request):
    _require_payout_role(request.user)
    payable_ids = request.data.get("payable_ids", [])
    request_key = request.data.get("request_key")
    if (
        not isinstance(payable_ids, list)
        or not payable_ids
        or any(not isinstance(x, str) for x in payable_ids)
        or not request_key
    ):
        raise ValidationError("payable_ids and request_key are required.")
    operation = "payout.execute"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        from core_apps.users.models import User

        _require_payout_role(request.user, lock=True)
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        lease_ids = list(
            OwnerPayable.objects.filter(id__in=payable_ids)
            .values_list("lease_id", flat=True)
            .order_by()
            .distinct()
        )
        if len(lease_ids) != 1:
            raise ValidationError("A payout batch must target one lease.")
        from ..services.rental_lifecycle.locks import lock_financial_lease

        lease = lock_financial_lease(Lease.objects.get(pk=lease_ids[0]))
        evaluate_owner_payables(lease)
        payables = list(
            OwnerPayable.objects.select_for_update(of=("self",))
            .select_related("lease__owner")
            .filter(id__in=payable_ids)
        )
        if len(payables) != len(set(payable_ids)) or any(
            x.payout_status != "ready" for x in payables
        ):
            raise RentalConflict(
                "Every payable must be eligible and unallocated.", code="payout_held"
            )
        if (
            len({(x.invoice.beneficiary_id or x.lease.owner_id) for x in payables}) != 1
            or len({x.lease_id for x in payables}) != 1
        ):
            raise ValidationError("A payout batch must target one owner and lease.")
        batch = PayoutBatch.objects.create(
            approved_by=request.user, request_key=request_key
        )
        profile = OwnerPaymentProfile.objects.select_for_update().get(
            owner=(payables[0].invoice.beneficiary or payables[0].lease.owner)
        )
        if (
            not profile.payout_ready
            or profile.status != "ready"
            or not profile.provider_account_id
        ):
            raise RentalConflict(
                "The reviewed beneficiary is not ready.", code="payout_held"
            )
        from core_apps.users.services.sensitive_actions import consume

        consume(
            request,
            action="payout.execute",
            resource_id=lease.id,
            revision=lease.revision,
            payload={
                "command": request.data,
                "amount_minor": sum(x.net_minor for x in payables),
                "currency": "EGP",
                "beneficiary_revision": profile.revision,
                "beneficiary_account_digest": fingerprint(profile.provider_account_id),
            },
        )
        payout = RentalPayout.objects.create(
            batch=batch,
            owner=(payables[0].invoice.beneficiary or payables[0].lease.owner),
            lease=payables[0].lease,
            amount_minor=sum(x.net_minor for x in payables),
            masked_beneficiary=profile.masked_beneficiary,
            beneficiary_profile_revision=profile.revision,
            beneficiary_provider=profile.provider,
            beneficiary_account_id=profile.provider_account_id,
        )
        payout.payables.set(payables)
        for payable in payables:
            payable.payout_status = "submitted"
            payable.revision += 1
            payable.save(update_fields=["payout_status", "revision", "updated_at"])
        PayoutAuditEvent.objects.create(
            payout=payout, actor=request.user, action="approved"
        )
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=payables[0].lease.id,
            result_subject_id=payout.id,
            result_revision=payout.revision,
            resource=payout_payload(payout),
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)
