"""Rental phase4 views: operations reconcile payout."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import Lease, PaymobPayout, PayoutAuditEvent, RentalPayout
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import remember_mutation, replay_operation
from ..services.rental_phase3 import post_ledger_transaction
from .handover_respond import payout_payload
from .operations_execute_payout import _require_payout_role


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def operations_reconcile_payout(request, payout_id):
    from .payout_review import _reader

    instruction = PaymobPayout.objects.filter(
        payout__id=payout_id, current=True
    ).first()
    if instruction:
        _reader(request.user)
    else:
        _require_payout_role(request.user)
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"payout.reconcile.{payout_id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    if instruction:
        from ..services.paymob_payouts import process

        # Reconciliation can only query an already submitted instruction.
        # It never sends a queued transfer or grants a replacement approval.
        process(instruction, allow_submit=False)
    with transaction.atomic():
        if instruction:
            _reader(request.user)
        else:
            _require_payout_role(request.user, lock=True)
        candidate = get_object_or_404(RentalPayout, id=payout_id)
        from ..services.rental_lifecycle.locks import lock_financial_lease

        lock_financial_lease(Lease.objects.get(pk=candidate.lease_id))
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        payout = get_object_or_404(
            RentalPayout.objects.select_for_update().prefetch_related("payables"),
            id=payout_id,
        )
        if payout.status != RentalPayout.Status.PAID and not instruction:
            from ..services.rental_lifecycle.provider_instructions import (
                execute_local_instruction,
            )

            payout.provider_payout_id = execute_local_instruction(
                kind="payout",
                subject=payout,
                request_key=payout.batch.request_key,
                payload={
                    "amount_minor": payout.amount_minor,
                    "currency": payout.currency,
                    "beneficiary": payout.masked_beneficiary,
                },
            )
            payout.status = RentalPayout.Status.PAID
            payout.revision += 1
            payout.save()
            payout.payables.update(payout_status="succeeded", updated_at=timezone.now())
            post_ledger_transaction(
                reference=f"payout:{payout.id}",
                kind="owner_payout",
                lease=payout.lease,
                entries=[
                    ("owner_liability", "debit", payout.amount_minor),
                    ("platform_cash", "credit", payout.amount_minor),
                ],
            )
            PayoutAuditEvent.objects.create(
                payout=payout,
                actor=request.user,
                action="paid",
                metadata={"provider_payout_id": payout.provider_payout_id},
            )
            from ..services.payout_notifications import record

            record(payout, "paid")
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=payout.id,
            result_subject_id=payout.id,
            result_revision=payout.revision,
            resource=payout_payload(payout),
        )
    return Response(output)
