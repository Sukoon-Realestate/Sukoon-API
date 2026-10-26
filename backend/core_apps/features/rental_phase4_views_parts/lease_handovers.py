"""Rental phase4 views: lease handovers."""

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import Lease, RentalHandover
from ..renderers import FeatureJsonRenderer
from ..services.lease_permissions import handover_actions
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .handover_payload import (
    _money,
    _lease,
    handover_payload,
    _handover,
    _validate_evidence,
)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
@parser_classes([JSONParser])
def lease_handovers(request, lease_id):
    lease = _lease(request, lease_id)
    if request.method == "GET":
        items = [
            handover_payload(x, request.user)
            for x in lease.handovers.prefetch_related("evidence").all()
        ]
        return Response(
            {"count": len(items), "next": None, "previous": None, "results": items}
        )
    required = {
        "kind",
        "possession_on",
        "condition",
        "keys",
        "meters",
        "inventory",
        "evidence_ids",
        "request_key",
        "expected_revision",
    }
    if not required.issubset(request.data):
        raise ValidationError({"request": f"Required: {', '.join(sorted(required))}."})
    if (
        request.data["kind"] not in RentalHandover.Kind.values
        or int(request.data["expected_revision"]) != 0
    ):
        raise ValidationError("Invalid handover kind or initial revision.")
    operation = f"handover.create.{lease.id}.{request.data['kind']}"
    replay = replay_operation(
        request.user, operation, request.data["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    evidence = _validate_evidence(lease, request.data["evidence_ids"])
    with transaction.atomic():
        lease = _lease(request, lease_id, lock=True)
        if (
            not request.user.is_active
            or not request.user.is_verified
            or lease.legacy_read_only
        ):
            raise PermissionDenied(
                "A verified participant and a supported agreement are required."
            )
        if lease.status not in {
            Lease.Status.ACTIVE,
            Lease.Status.TERMINATION_PENDING,
            Lease.Status.ENDED,
        }:
            raise RentalConflict("Handover requires a paid active agreement.")
        if request.data["kind"] == "move_in" and lease.status != Lease.Status.ACTIVE:
            raise RentalConflict("Move-in requires an active agreement.")
        replay = replay_operation(
            request.user, operation, request.data["request_key"], request.data
        )
        if replay:
            return Response(replay[0], status=replay[1])
        if lease.handovers.filter(kind=request.data["kind"]).exists():
            raise RentalConflict("This handover already exists.")
        handover = RentalHandover.objects.create(
            lease=lease,
            kind=request.data["kind"],
            status=RentalHandover.Status.PENDING_APPROVAL,
            possession_on=request.data["possession_on"],
            condition=request.data["condition"],
            keys=request.data["keys"],
            meters=request.data["meters"],
            inventory=request.data["inventory"],
        )
        handover.evidence.set(evidence)
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request.data["request_key"],
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=handover.id,
            result_revision=handover.revision,
            resource=handover_payload(handover, request.user),
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def handover_detail(request, handover_id):
    handover = _handover(request, handover_id)
    if request.method == "GET":
        return Response(handover_payload(handover, request.user))
    expected = int(request.data.get("expected_revision", 0))
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"handover.update.{handover.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        handover = _handover(request, handover_id, lock=True)
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        if handover.revision != expected:
            raise RentalConflict("Handover revision conflict.", code="stale_revision")
        if "edit_handover" not in handover_actions(request.user, handover):
            raise RentalConflict("This handover cannot be edited.")
        evidence = _validate_evidence(
            handover.lease, request.data.get("evidence_ids", [])
        )
        for field in ("possession_on", "condition", "keys", "meters", "inventory"):
            if field in request.data:
                setattr(handover, field, request.data[field])
        handover.approvals = []
        handover.status = RentalHandover.Status.PENDING_APPROVAL
        handover.revision += 1
        handover.save()
        handover.evidence.set(evidence)
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=handover.id,
            result_subject_id=handover.id,
            result_revision=handover.revision,
            resource=handover_payload(handover, request.user),
        )
    return Response(output)


def deposit_payload(deposit):
    remaining = max(
        deposit.collected_minor - deposit.returned_minor - deposit.applied_minor, 0
    )
    return {
        "id": str(deposit.id),
        "lease_id": str(deposit.lease.id),
        "revision": deposit.revision,
        "holder": deposit.lease.terms.get("deposit_holder", "platform"),
        "invoice_id": str(deposit.invoice.id) if deposit.invoice else None,
        "status": "collected" if deposit.collected_minor else "due",
        "agreed": _money(deposit.agreed_minor),
        "due": _money(deposit.due_minor),
        "collected": _money(deposit.collected_minor),
        "returned": _money(deposit.returned_minor),
        "applied": _money(deposit.applied_minor),
        "disputed": _money(deposit.disputed_minor),
        "remaining": _money(remaining),
    }
