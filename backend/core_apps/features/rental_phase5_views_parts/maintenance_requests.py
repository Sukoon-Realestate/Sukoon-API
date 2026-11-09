"""Rental phase5 views: maintenance requests."""

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import MaintenanceEvent, MaintenanceRequest
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import remember_mutation, replay_operation
from .maintenance_payload import (
    _lease,
    _safe_evidence,
    maintenance_payload,
    _maintenance,
)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def maintenance_requests(request, lease_id):
    lease = _lease(request, lease_id, servicing=True)
    if request.method == "GET":
        results = [
            maintenance_payload(x, request.user)
            for x in lease.maintenance_requests.prefetch_related("events", "evidence")
        ]
        return Response(
            {"count": len(results), "next": None, "previous": None, "results": results}
        )
    from ..rental_serializers_parts.command_serializers import (
        MaintenanceCreateCommand,
        validated,
    )

    # A3-02: the complete body is typed before authority, replay or writes.
    command = validated(MaintenanceCreateCommand, request.data)
    from ..services.cycle_permissions import cycle_actions
    from rest_framework.exceptions import PermissionDenied
    if "create_maintenance_request" not in cycle_actions(request.user, lease):
        raise PermissionDenied("Maintenance requires an existing serviceable agreement.")
    operation = f"maintenance.create.{lease.id}"
    replay = replay_operation(
        request.user, operation, command["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    evidence = _safe_evidence(lease, command["evidence_ids"])
    with transaction.atomic():
        lease = _lease(request, lease_id, lock=True, servicing=True)
        if "create_maintenance_request" not in cycle_actions(request.user, lease):
            raise PermissionDenied("Maintenance requires an existing serviceable agreement.")
        replay = replay_operation(
            request.user, operation, command["request_key"], request.data
        )
        if replay:
            return Response(replay[0], status=replay[1])
        from core_apps.common.command_authority import recheck_session

        recheck_session(request)
        item = MaintenanceRequest.objects.create(
            lease=lease,
            reporter=request.user,
            title=command["title"],
            description=command["description"],
            category=command["category"],
            priority=command["priority"],
            access_times=command["access_times"],
        )
        item.evidence.set(evidence)
        MaintenanceEvent.objects.create(
            maintenance_request=item, actor=request.user, action="created"
        )
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=command["request_key"],
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=maintenance_payload(item, request.user),
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def maintenance_detail(request, request_id):
    return Response(
        maintenance_payload(_maintenance(request, request_id), request.user)
    )
