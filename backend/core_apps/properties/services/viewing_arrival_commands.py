"""Appointment authority, revision and receipt boundary; no HTTP response objects."""

from django.db import transaction
from core_apps.users.models import User
from rest_framework.exceptions import PermissionDenied
from core_apps.common.idempotency import execute_idempotent, IdempotencyConflict
from core_apps.users.services.sessions import validate_session
from ..models import ViewingArrival
from .viewing_times import locked_visit
from .viewing_arrival import arrival_payload, notify_arrival
from ..serializers.appointment_commands import ArrivalCommand


def manage_arrival(
    user, visit_id, payload=None, *, method="GET", auth=None, expected_revision=None
):
    with transaction.atomic():
        visit = locked_visit(visit_id, user)
        user = User.objects.get(pk=user.pk)
        if auth:
            validate_session(user, auth)
        if method == "GET":
            return (arrival_payload(visit, user), 200)
        if user.pk != visit.property.owner_id:
            raise PermissionDenied("Only the owner may edit arrival instructions.")
        body = ArrivalCommand(data=payload)
        body.is_valid(raise_exception=True)
        data = body.validated_data

        def apply():
            if (
                visit.status != "confirmed"
                or visit.revision != data["expected_visit_revision"]
            ):
                raise IdempotencyConflict(
                    "The viewing changed. Refresh before sharing directions."
                )
            row = ViewingArrival.objects.filter(visit=visit).first()
            if (row.revision if row else 0) != data["expected_revision"]:
                raise IdempotencyConflict(
                    "Arrival directions changed. Refresh and review them."
                )
            values = {
                key: data[key]
                for key in [
                    "active",
                    "meeting_point",
                    "entrance",
                    "instructions",
                    "latitude",
                    "longitude",
                ]
            }
            if row:
                for key, value in values.items():
                    setattr(row, key, value)
                row.revision += 1
                row.save()
            else:
                row = ViewingArrival.objects.create(visit=visit, **values)
            visit._state.fields_cache.pop("arrival_card", None)
            notify_arrival(visit, row.revision)
            return (arrival_payload(visit, user), 200, row.id)

        result, code, _ = execute_idempotent(
            user=user,
            operation=f"viewing.arrival:{visit_id}",
            key=str(data["request_key"]),
            payload=data,
            action=apply,
        )
        return (result, code)
