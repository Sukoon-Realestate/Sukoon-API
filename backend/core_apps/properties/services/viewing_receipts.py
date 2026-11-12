"""Appointment command execution and scoped recovery projections."""

from uuid import UUID
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from core_apps.common.idempotency import execute_idempotent, resolve_or_close
from core_apps.features.models import IdempotencyRecord
from ..models import PropertyVisit
from ..serializers import (
    TenantVisitRequestDetailSerializer,
    OwnerVisitRequestDetailSerializer,
)
from ..serializers.appointment_commands import ViewingCommandBody
from .viewing_access import can_read
from .viewing_commands import command


def visit_projection(visit, user, context):
    serializer = (
        OwnerVisitRequestDetailSerializer
        if visit.property.owner_id == user.pk
        else TenantVisitRequestDetailSerializer
    )
    return serializer(visit, context=context).data


def execute_command(actor, id, payload, *, auth=None, context=None):
    body = ViewingCommandBody(data=payload)
    body.is_valid(raise_exception=True)
    visit = get_object_or_404(PropertyVisit, id=id)
    if not can_read(visit, actor):
        raise NotFound()

    def apply():
        result = command(actor, id, body.validated_data)
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
        user=actor,
        operation=f"viewing.command:{id}",
        key=str(body.validated_data["request_key"]),
        payload=body.validated_data,
        action=apply,
        request_subject_id=id,
        auth_claims=auth,
    )
    visit.refresh_from_db()
    if not can_read(visit, actor):
        raise NotFound()
    return ({**data, "visit": visit_projection(visit, actor, context)}, status)


def read_command(actor, id, request_key, *, auth=None, context=None):
    visit = get_object_or_404(PropertyVisit, id=id)
    if not can_read(visit, actor):
        raise NotFound()
    try:
        key = str(UUID(request_key))
    except ValueError:
        raise ValidationError({"request_key": "Use the original request UUID."})
    record = IdempotencyRecord.objects.filter(
        user=actor, request_key=key, operation=f"viewing.command:{id}"
    ).first()
    return (
        {
            "request_key": key,
            "status": record.recovery_status if record else "not_found",
            "action": record.response_data.get("action", "") if record else "",
            "visit": visit_projection(visit, actor, context) if record else None,
        },
        200,
    )


def resolve_command(actor, id, payload, *, auth=None, context=None):
    visit = get_object_or_404(PropertyVisit, id=id)
    if not can_read(visit, actor):
        raise NotFound()
    field = serializers.UUIDField()
    key = str(field.run_validation(payload.get("request_key")))
    with transaction.atomic():
        record = resolve_or_close(
            user=actor, operation=f"viewing.command:{id}", key=key, auth_claims=auth
        )
        visit.refresh_from_db()
        if not can_read(visit, actor):
            raise NotFound()
        return (
            {
                "request_key": key,
                "status": record.recovery_status,
                "action": record.response_data.get("action", ""),
                "visit": visit_projection(visit, actor, context),
            },
            200,
        )


def creation_receipt(actor, request_key, *, auth=None, context=None):
    try:
        key = str(UUID(request_key))
    except ValueError:
        raise ValidationError({"request_key": "Use the original request UUID."})
    with transaction.atomic():
        record = (
            IdempotencyRecord.objects.filter(user=actor, request_key=key)
            .filter(operation__startswith="property.visit.create:")
            .first()
        )
        if not record:
            return ({"request_key": key, "status": "not_found"}, 200)
        visit = get_object_or_404(PropertyVisit, id=record.result_subject_id)
        if not can_read(visit, actor):
            raise NotFound()
        return (
            {
                "request_key": key,
                "status": "confirmed",
                "visit": TenantVisitRequestDetailSerializer(
                    visit, context=context
                ).data,
            },
            200,
        )
