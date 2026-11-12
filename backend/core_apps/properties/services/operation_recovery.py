"""Recover an authoritative listing receipt or fence an uncommitted write."""

from django.shortcuts import get_object_or_404
from django.db import transaction
from core_apps.users.models import User
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import UUIDField
from core_apps.common.idempotency import resolve_or_close
from ..models import Property


@transaction.atomic
def resolve_listing_operation(actor, payload, *, auth=None, idempotency_key=None):
    User.objects.select_for_update().get(pk=actor.pk)
    kind, identity = (payload.get("kind"), payload.get("property_id"))
    if kind not in {"create", "update", "image.upload"}:
        raise ValidationError("Unsupported property command.")
    if kind != "create":
        identity = UUIDField().run_validation(identity)
        subject = get_object_or_404(
            Property.objects.select_for_update(), id=identity, owner=actor
        )
        identity = str(subject.id)
    operation = "property.create" if kind == "create" else f"property.{kind}:{identity}"
    key = idempotency_key
    record = resolve_or_close(
        user=actor, operation=operation, key=key, auth_claims=auth
    )
    if record.result_subject_id and kind == "create":
        get_object_or_404(Property, id=record.result_subject_id, owner=actor)
    outcome = (
        "acknowledged"
        if record.recovery_status == "confirmed"
        else record.recovery_status
    )
    return {
        "request_key": key,
        "outcome": outcome,
        "resource": record.response_data if outcome == "acknowledged" else None,
    }
