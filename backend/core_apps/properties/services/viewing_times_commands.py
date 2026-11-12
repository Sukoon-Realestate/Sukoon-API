"""Appointment authority, revision and receipt boundary; no HTTP response objects."""

from django.db import transaction
from core_apps.users.models import User
from core_apps.common.idempotency import execute_idempotent
from core_apps.users.services.sessions import validate_session
from .viewing_times import locked_visit, snapshot, command
from ..serializers.appointment_commands import ViewingTimeCommand


def manage_time_proposals(
    user, visit_id, payload=None, *, method="GET", auth=None, expected_revision=None
):
    with transaction.atomic():
        visit = locked_visit(visit_id, user)
        user = User.objects.get(pk=user.pk)
        if auth:
            validate_session(user, auth)
        if method == "GET":
            return (snapshot(visit), 200)
        body = ViewingTimeCommand(data=payload)
        body.is_valid(raise_exception=True)
        data = body.validated_data

        def apply():
            return (command(visit, user, data), 200, visit.id)

        result, code, _ = execute_idempotent(
            user=user,
            operation=f"viewing.times:{visit_id}",
            key=str(data["request_key"]),
            payload=data,
            action=apply,
        )
        return (result, code)
