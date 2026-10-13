"""Rental phase6 views: final settlement propose."""

import uuid
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import FinalSettlement, Lease, PrivateAccessRevocation, RentalEvidence
from ..providers import require_rental_provider
from ..renderers import FeatureJsonRenderer
from ..services.cycle_permissions import cycle_actions
from ..services.commands import command_identity, money_minor
from ..services.settlements import LINE_TYPES, financial_snapshot, prepare_settlement
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation


def _money(value):
    return {"amount_minor": value, "currency": "EGP", "exponent": 2}


def _lease(request, lease_id, lock=False):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        require_rental_provider(request.user)
    queryset = Lease.objects.select_related("owner", "tenant", "property")
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    lease = get_object_or_404(queryset, id=lease_id)
    if request.user not in (lease.owner, lease.tenant):
        raise NotFound()
    if PrivateAccessRevocation.objects.filter(lease=lease, user=request.user).exists():
        raise NotFound()
    return lease


def settlement_payload(item, user=None):
    return {
        "allowed_actions": cycle_actions(user, item),
        "blocking_reasons": [],
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "status": item.status,
        "lines": item.lines,
        "rent_balance": _money(item.rent_balance_minor),
        "deposit_to_return": _money(item.deposit_to_return_minor),
        "refund_due": _money(item.refund_due_minor),
        "total_due": _money(item.total_due_minor),
        "accepted_by": item.accepted_by,
        "disputed_item_ids": item.disputed_item_ids,
        "execution_status": item.execution_status,
        "execution_plan": item.execution_plan,
        "executed_at": item.executed_at.isoformat() if item.executed_at else None,
        "history": item.history,
    }


def _settlement(lease):
    item, _ = FinalSettlement.objects.get_or_create(lease=lease)
    return item


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def final_settlement_detail(request, lease_id):
    return Response(
        settlement_payload(_settlement(_lease(request, lease_id)), request.user)
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def final_settlement_propose(request, lease_id):
    lease = _lease(request, lease_id)
    request_key, expected_revision = command_identity(request.data, minimum=1)
    operation = f"settlement.propose.{lease.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    lines = []
    seen = set()
    if (
        not isinstance(request.data.get("lines", []), list)
        or len(request.data.get("lines", [])) > 100
    ):
        raise ValidationError({"lines": "Supply at most 100 settlement lines."})
    for raw in request.data.get("lines", []):
        if not isinstance(raw, dict):
            raise ValidationError({"lines": "Each line must be an object."})
        line_id = str(raw.get("id") or uuid.uuid4())
        amount = money_minor(raw.get("amount"), allow_negative=True)
        if (
            line_id in seen
            or raw.get("type") not in LINE_TYPES
            or not isinstance(amount, int)
        ):
            raise ValidationError(
                {
                    "lines": "Each line needs a unique ID, supported type, and integer EGP amount."
                }
            )
        evidence_ids = raw.get("evidence_ids", [])
        if RentalEvidence.objects.filter(
            id__in=evidence_ids,
            lease=lease,
            malware_status=RentalEvidence.MalwareStatus.SAFE,
        ).count() != len(set(evidence_ids)):
            raise ValidationError(
                {"lines": "Line evidence must be safe and belong to this lease."}
            )
        seen.add(line_id)
        lines.append(
            {
                "id": line_id,
                "type": raw["type"],
                "label": raw.get("label", raw["type"]),
                "description": raw.get("description")
                or raw.get("label")
                or raw["type"],
                "amount": _money(amount),
                "evidence_ids": list(evidence_ids),
                **(
                    {"invoice_id": str(raw["invoice_id"])}
                    if raw.get("invoice_id")
                    else {}
                ),
            }
        )
    with transaction.atomic():
        lease = _lease(request, lease_id, lock=True)
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        item = _settlement(lease)
        if item.revision != expected_revision:
            raise RentalConflict("Settlement revision conflict.", code="stale_revision")
        if item.status == FinalSettlement.Status.ACCEPTED:
            raise RentalConflict("An accepted settlement cannot be rewritten.")
        plan = prepare_settlement(lease, lines)
        item.history.append(
            {
                "revision": item.revision,
                "status": item.status,
                "lines": item.lines,
                "accepted_by": item.accepted_by,
                "disputed_item_ids": item.disputed_item_ids,
            }
        )
        item.lines = lines
        item.financial_snapshot = financial_snapshot(lease)
        item.execution_plan = plan
        for field in (
            "rent_balance_minor",
            "deposit_to_return_minor",
            "refund_due_minor",
            "total_due_minor",
        ):
            setattr(item, field, plan[field])
        item.status = FinalSettlement.Status.PROPOSED
        item.accepted_by = [str(request.user.id)]
        item.disputed_item_ids = []
        item.proposed_by = request.user
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
            resource=settlement_payload(item, request.user),
        )
    return Response(output)
