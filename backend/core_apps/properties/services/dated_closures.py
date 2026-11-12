from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.common.idempotency import (
    fingerprint,
    IdempotencyConflict,
    execute_idempotent,
)
from core_apps.users.models import User
from core_apps.users.services.sessions import validate_session
from ..models import Property, AvailabilityClosure
from .availability_closures import parse_range, affected_visits
from uuid import UUID


def project(row):
    from zoneinfo import ZoneInfo

    zone = ZoneInfo(row.timezone)
    return {
        "id": str(row.id),
        "starts_at": row.starts_at.astimezone(zone).isoformat(),
        "ends_at": row.ends_at.astimezone(zone).isoformat(),
        "timezone": row.timezone,
        "revision": row.revision,
        "retained_visits": row.retained_visits,
    }


def manage_dated_closures(
    user, property_id, data, *, method, auth=None, idempotency_key=None
):
    """Serialize account/listing, compare preview, retain appointments and receipt.

    POST only previews; PUT requires a key and a current preview/revision.
    """
    with transaction.atomic():
        actor = User.objects.select_for_update().get(pk=user.pk)
        if not actor.is_active or actor.closed_at:
            raise PermissionDenied()
        if auth:
            validate_session(actor, auth)
        prop = get_object_or_404(
            Property.objects.select_for_update(),
            id=property_id,
            owner=actor,
            retired_at__isnull=True,
        )
        if method == "GET":
            return {
                "protocol": 1,
                "closures": [
                    project(row) for row in prop.dated_closures.filter(active=True)
                ],
            }, 200

        def operation():
            if data.get("action") == "remove":
                if method != "PUT":
                    raise ValidationError(
                        "Removing a closure requires an explicit commit."
                    )
                try:
                    identity = UUID(data.get("closure_id", ""))
                except (ValueError, TypeError, AttributeError):
                    raise ValidationError("Select a valid closure.")
                row = get_object_or_404(AvailabilityClosure, property=prop, id=identity)
                if data.get("expected_revision") != row.revision:
                    raise IdempotencyConflict("The closure changed. Refresh it.")
                row.active = False
                row.revision += 1
                row.save(update_fields=["active", "revision", "updated_at"])
                return {"protocol": 1, "removed": str(row.id)}, 200, row.id
            start, end, zone = parse_range(data)
            visits = affected_visits(prop, start, end)
            preview = {
                "protocol": 1,
                "starts_at": start.isoformat(),
                "ends_at": end.isoformat(),
                "timezone": str(zone),
                "affected_visits": visits,
            }
            preview["revision"] = fingerprint(
                {
                    "property": str(prop.id),
                    **preview,
                    "closures": list(
                        prop.dated_closures.values_list("id", "revision", "active")
                    ),
                }
            )
            if method == "POST":
                return preview, 200, None
            if data.get("revision") != preview["revision"]:
                raise IdempotencyConflict(
                    "Availability or an appointment changed. Preview again."
                )
            decisions = data.get("decisions", {})
            if not isinstance(decisions, dict) or decisions != {
                v["id"]: "keep" for v in visits
            }:
                raise ValidationError(
                    "Explicitly keep each existing appointment, or arrange its change before closing these times."
                )
            row = AvailabilityClosure.objects.create(
                property=prop,
                starts_at=start,
                ends_at=end,
                timezone=str(zone),
                retained_visits=visits,
            )
            return {"protocol": 1, "closure": project(row)}, 200, row.id

        if method == "POST":
            body, code, _ = operation()
        else:
            key = idempotency_key
            if not key:
                raise ValidationError("An Idempotency-Key is required.")
            body, code, _ = execute_idempotent(
                user=actor,
                operation="property.availability-closure",
                key=key,
                payload={"property": str(prop.id), **dict(data)},
                action=operation,
            )
        return body, code
