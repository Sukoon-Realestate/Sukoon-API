"""One recoverable listing command shared by every scalar update alias."""

from django.db import transaction
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import PermissionDenied
from core_apps.common.idempotency import execute_idempotent, IdempotencyConflict
from .listing_lock import lock_listing


def update_listing(
    *, instance, actor, auth_claims, command, expected_updated_at, key, context, partial=True
):
    # Fingerprint original inputs, including file bytes, before validation assigns
    # inventory identities or the mutable listing changes.
    payload = (
        {
            name: (command.getlist(name) if len(command.getlist(name)) > 1 else command.get(name))
            for name in command
        }
        if hasattr(command, "getlist")
        else dict(command)
    )
    payload["expected_updated_at"] = expected_updated_at or ""
    if not partial:
        payload["full_update"] = True

    def apply():
        from ..serializers import PropertySerializer, PropertyDetailSerializer

        with transaction.atomic():
            current = lock_listing(instance.pk)
            request = context.get("request")
            if request is not None:
                from core_apps.common.command_authority import recheck_session

                recheck_session(request)
            if current.owner_id != actor.pk:
                raise PermissionDenied("Only the current owner can edit a listing.")
            try:
                matches = (
                    not expected_updated_at
                    or parse_datetime(expected_updated_at) == current.updated_at
                )
            except (ValueError, TypeError):
                matches = False
            if not matches:
                raise IdempotencyConflict("Property changed. Reload and review before saving.")
            serializer = PropertySerializer(current, data=command, partial=partial, context=context)
            serializer.is_valid(raise_exception=True)
            updated = serializer.save()
            data = PropertyDetailSerializer(updated, context=context).data
            return {"message": "Property changes submitted for review.", **data}, 200, updated.id

    return execute_idempotent(
        user=actor,
        auth_claims=auth_claims,
        operation=f"property.update:{instance.id}",
        key=key,
        payload=payload,
        action=apply,
        request_subject_id=instance.id,
    )
