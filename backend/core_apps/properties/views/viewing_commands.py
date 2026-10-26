from uuid import UUID
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from core_apps.common.idempotency import execute_idempotent, resolve_or_close
from core_apps.features.models import IdempotencyRecord
from ..models import PropertyVisit
from ..serializers import (
    TenantVisitRequestDetailSerializer,
    OwnerVisitRequestDetailSerializer,
)
from ..services.viewing_access import can_read
from ..services.viewing_commands import command
from .post_visit_decision import PostVisitJsonRenderer


class ViewingCommandBody(serializers.Serializer):
    request_key = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=1)
    action = serializers.ChoiceField(choices=["reassign", "accept", "reject", "cancel"])
    representative_membership_id = serializers.UUIDField(required=False)
    note = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=100)
    custom_reason = serializers.CharField(
        required=False, allow_blank=True, max_length=1000
    )

    def validate(self, data):
        if data["action"] == "reassign" and not data.get(
            "representative_membership_id"
        ):
            raise ValidationError(
                {
                    "representative_membership_id": "Choose the current company representative."
                }
            )
        if data["action"] != "reassign" and data.get("representative_membership_id"):
            raise ValidationError(
                {
                    "representative_membership_id": "Only reassignment changes the representative."
                }
            )
        return data


def visit_projection(visit, request):
    serializer = (
        OwnerVisitRequestDetailSerializer
        if visit.property.owner_id == request.user.pk
        else TenantVisitRequestDetailSerializer
    )
    return serializer(visit, context={"request": request}).data


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([PostVisitJsonRenderer])
def viewing_command(request, id):
    visit = get_object_or_404(PropertyVisit, id=id)
    if not can_read(visit, request.user):
        raise NotFound()
    if request.method == "GET":
        try:
            key = str(UUID(request.query_params.get("request_key", "")))
        except ValueError:
            raise ValidationError({"request_key": "Use the original request UUID."})
        record = IdempotencyRecord.objects.filter(
            user=request.user, request_key=key, operation=f"viewing.command:{id}"
        ).first()
        return Response(
            {
                "request_key": key,
                "status": record.recovery_status if record else "not_found",
                "action": record.response_data.get("action", "") if record else "",
                "visit": (visit_projection(visit, request) if record else None),
            }
        )
    return execute_viewing_command(request, id, request.data)


def execute_viewing_command(request, id, payload):
    body = ViewingCommandBody(data=payload)
    body.is_valid(raise_exception=True)
    visit = get_object_or_404(PropertyVisit, id=id)
    if not can_read(visit, request.user):
        raise NotFound()

    def apply():
        result = command(request.user, id, body.validated_data)
        return (
            {
                "id": str(result.id),
                "revision": result.revision,
                "request_key": str(body.validated_data["request_key"]),
                "action": body.validated_data["action"],
                "status": "confirmed",
            },
            200,
            result.id,
        )

    data, status, replay = execute_idempotent(
        user=request.user,
        operation=f"viewing.command:{id}",
        key=str(body.validated_data["request_key"]),
        payload=body.validated_data,
        action=apply,
        request_subject_id=id,
        auth_claims=request.auth,
    )
    visit.refresh_from_db()
    if not can_read(visit, request.user):
        raise NotFound()
    return Response(
        {
            **data,
            "visit": visit_projection(visit, request),
        },
        status=status,
    )


def execute_visit_response(request, id, action):
    result = execute_viewing_command(request, id, {**request.data, "action": action})
    return Response(
        {
            **result.data["visit"],
            "operation": {
                key: result.data[key] for key in ("request_key", "action", "status")
            },
        },
        status=result.status_code,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([PostVisitJsonRenderer])
def resolve_viewing_command(request, id):
    visit = get_object_or_404(PropertyVisit, id=id)
    if not can_read(visit, request.user):
        raise NotFound()
    field = serializers.UUIDField()
    key = str(field.run_validation(request.data.get("request_key")))
    with transaction.atomic():
        record = resolve_or_close(
            user=request.user,
            operation=f"viewing.command:{id}",
            key=key,
            auth_claims=request.auth,
        )
        visit.refresh_from_db()
        if not can_read(visit, request.user):
            raise NotFound()
        return Response(
            {
                "request_key": key,
                "status": record.recovery_status,
                "action": record.response_data.get("action", ""),
                "visit": visit_projection(visit, request),
            }
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([PostVisitJsonRenderer])
def viewing_receipt(request):
    try:
        key = str(UUID(request.query_params.get("request_key", "")))
    except ValueError:
        raise ValidationError({"request_key": "Use the original request UUID."})
    with transaction.atomic():
        record = (
            IdempotencyRecord.objects.filter(user=request.user, request_key=key)
            .filter(operation__startswith="property.visit.create:")
            .first()
        )
        if not record:
            return Response({"request_key": key, "status": "not_found"})
        visit = get_object_or_404(PropertyVisit, id=record.result_subject_id)
        if not can_read(visit, request.user):
            raise NotFound()
        return Response(
            {
                "request_key": key,
                "status": "confirmed",
                "visit": TenantVisitRequestDetailSerializer(
                    visit, context={"request": request}
                ).data,
            }
        )
