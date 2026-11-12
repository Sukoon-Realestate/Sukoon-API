"""Appointment authority, revision and receipt boundary; no HTTP response objects."""

from django.db import transaction
from core_apps.users.models import User
from rest_framework.exceptions import ValidationError
from core_apps.common.idempotency import IdempotencyConflict
from core_apps.users.services.sessions import validate_session
from .viewing_times import locked_visit


def message_context(
    user, visit_id, payload=None, *, method="GET", auth=None, expected_revision=None
):
    with transaction.atomic():
        visit = locked_visit(visit_id, user)
        user = User.objects.get(pk=user.pk)
        if auth:
            validate_session(user, auth)
        if (
            visit.status != "confirmed"
            or visit.visit_date is None
            or visit.visit_time is None
        ):
            raise IdempotencyConflict(
                "An arrival-delay draft needs a confirmed appointment with an agreed time."
            )
        expected = expected_revision
        if expected is not None:
            try:
                expected = int(expected)
            except (ValueError, TypeError):
                raise ValidationError("Supply the viewing revision you reviewed.")
            if expected != visit.revision:
                raise IdempotencyConflict(
                    "The appointment changed. Review its current time before preparing a message."
                )
        other = (
            visit.tenant if visit.property.owner_id == user.pk else visit.property.owner
        )
        return (
            {
                "protocol": 1,
                "visit_id": str(visit.id),
                "revision": visit.revision,
                "property_id": str(visit.property.id),
                "property_title": visit.property.title,
                "offer_id": visit.offer_id,
                "offer_name": (visit.offer_snapshot or {}).get("name", ""),
                "date": visit.visit_date.isoformat(),
                "time": visit.visit_time.strftime("%H:%M"),
                "timezone": "Africa/Cairo",
                "other_user_id": str(other.id),
            },
            200,
        )
