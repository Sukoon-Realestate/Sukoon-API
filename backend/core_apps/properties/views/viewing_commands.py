from uuid import UUID
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from core_apps.common.idempotency import execute_idempotent
from core_apps.features.models import IdempotencyRecord
from ..models import PropertyVisit
from ..serializers import TenantVisitRequestDetailSerializer
from ..services.viewing_access import can_read
from ..services.viewing_commands import command
from .post_visit_decision import PostVisitJsonRenderer


class ViewingCommandBody(serializers.Serializer):
    request_key = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=1)
    action = serializers.ChoiceField(choices=["reschedule", "reassign"])
    representative_membership_id = serializers.UUIDField(required=False)
    visit_date = serializers.DateField(required=False)
    visit_time = serializers.TimeField(required=False)
    note = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate(self, attrs):
        required = (
            ["representative_membership_id"]
            if attrs["action"] == "reassign"
            else ["visit_date", "visit_time"]
        )
        if any(key not in attrs for key in required):
            raise serializers.ValidationError("Supply the required action fields.")
        return attrs


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
                "status": "confirmed" if record else "not_found",
                "visit": (
                    TenantVisitRequestDetailSerializer(
                        visit, context={"request": request}
                    ).data
                    if record
                    else None
                ),
            }
        )
    body = ViewingCommandBody(data=request.data)
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
    )
    visit.refresh_from_db()
    if not can_read(visit, request.user):
        raise NotFound()
    return Response(
        {
            **data,
            "visit": TenantVisitRequestDetailSerializer(
                visit, context={"request": request}
            ).data,
        },
        status=status,
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
