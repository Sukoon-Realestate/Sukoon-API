"""Rental phase5 views: maintenance requests."""

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import MaintenanceEvent, MaintenanceRequest
from ..renderers import FeatureJsonRenderer
from ..rental_serializers_parts.maintenance_cost_decision_serializer import (
    MaintenanceAccessTimesSerializer,
)
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
    required = {
        "title",
        "description",
        "category",
        "priority",
        "access_times",
        "evidence_ids",
        "request_key",
        "expected_revision",
    }
    if (
        not required.issubset(request.data)
        or int(request.data["expected_revision"]) != 0
    ):
        raise ValidationError(
            "Complete maintenance body with expected_revision=0 is required."
        )
    from ..services.cycle_permissions import cycle_actions
    from rest_framework.exceptions import PermissionDenied
    if "create_maintenance_request" not in cycle_actions(request.user, lease):
        raise PermissionDenied("Maintenance requires an existing serviceable agreement.")
    operation = f"maintenance.create.{lease.id}"
    replay = replay_operation(
        request.user, operation, request.data["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    access = MaintenanceAccessTimesSerializer(data=request.data)
    access.is_valid(raise_exception=True)
    evidence = _safe_evidence(lease, request.data["evidence_ids"])
    with transaction.atomic():
        lease = _lease(request, lease_id, lock=True, servicing=True)
        if "create_maintenance_request" not in cycle_actions(request.user, lease):
            raise PermissionDenied("Maintenance requires an existing serviceable agreement.")
        replay = replay_operation(
            request.user, operation, request.data["request_key"], request.data
        )
        if replay:
            return Response(replay[0], status=replay[1])
        item = MaintenanceRequest.objects.create(
            lease=lease,
            reporter=request.user,
            title=request.data["title"],
            description=request.data["description"],
            category=request.data["category"],
            priority=request.data["priority"],
            access_times=access.validated_data["access_times"],
        )
        item.evidence.set(evidence)
        MaintenanceEvent.objects.create(
            maintenance_request=item, actor=request.user, action="created"
        )
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request.data["request_key"],
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
