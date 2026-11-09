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
    from ..rental_serializers_parts.command_serializers import (
        HandoverCreateCommand,
        validated,
    )

    # A4-03: type the complete body before replay, locks or writes.
    command = validated(HandoverCreateCommand, request.data)
    operation = f"handover.create.{lease.id}.{command['kind']}"
    replay = replay_operation(
        request.user, operation, command["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    evidence = _validate_evidence(lease, command["evidence_ids"])
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
        if command["kind"] == "move_in" and lease.status != Lease.Status.ACTIVE:
            raise RentalConflict("Move-in requires an active agreement.")
        replay = replay_operation(
            request.user, operation, command["request_key"], request.data
        )
        if replay:
            return Response(replay[0], status=replay[1])
        from core_apps.common.command_authority import recheck_session

        recheck_session(request)
        if lease.handovers.filter(kind=command["kind"]).exists():
            raise RentalConflict("This handover already exists.")
        handover = RentalHandover.objects.create(
            lease=lease,
            kind=command["kind"],
            status=RentalHandover.Status.PENDING_APPROVAL,
            possession_on=command["possession_on"],
            condition=command["condition"],
            keys=command["keys"],
            meters=command["meters"],
            inventory=command["inventory"],
        )
        handover.evidence.set(evidence)
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=command["request_key"],
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
    from ..rental_serializers_parts.command_serializers import (
        HandoverUpdateCommand,
        validated,
    )

    command = validated(HandoverUpdateCommand, request.data)
    expected = command["expected_revision"]
    request_key = command["request_key"]
    operation = f"handover.update.{handover.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        handover = _handover(request, handover_id, lock=True)
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        from core_apps.common.command_authority import recheck_session

        recheck_session(request)
        if handover.revision != expected:
            raise RentalConflict("Handover revision conflict.", code="stale_revision")
        if "edit_handover" not in handover_actions(request.user, handover):
            raise RentalConflict("This handover cannot be edited.")
        evidence = _validate_evidence(handover.lease, command["evidence_ids"])
        for field in ("possession_on", "condition", "keys", "meters", "inventory"):
            if field in command:
                setattr(handover, field, command[field])
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
