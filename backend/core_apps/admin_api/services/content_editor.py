"""Current authority, version checks, audit and durable lost-response recovery."""

from django.core.exceptions import ValidationError as ModelValidationError
import uuid
from django.db import transaction, IntegrityError
from rest_framework.generics import get_object_or_404
from rest_framework.exceptions import ValidationError
from core_apps.admin_api.permissions import require_staff_actor
from core_apps.common.content_models import ContentEditAudit
from core_apps.common.idempotency import execute_idempotent, resolve_or_close
from core_apps.features.services.rental_phase2 import RentalConflict
from .content_registry import spec, validated, projection


def operation_name(kind, identity):
    suffix = "create" if identity is None else f"item:{identity}"
    return f"content.edit:{kind}:{suffix}"


@transaction.atomic
def edit(user, kind, identity, data, key, auth_claims=None):
    user = require_staff_actor(user, {"system_owner"}, lock=True)
    entry = spec(kind)
    if not key:
        raise ValidationError("Retain an operation key before saving content.")
    try:
        key = str(uuid.UUID(key))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("Use a UUID operation key.")
    operation = operation_name(kind, identity)

    def apply():
        from . import commerce_benefit_editor

        parent_plan = commerce_benefit_editor.lock_plan(kind, identity, data["values"])
        item = (
            get_object_or_404(
                entry.model.objects.select_for_update(),
                **{entry.identity_field: identity},
            )
            if identity
            else entry.model()
        )
        expected = data["expected_revision"]
        if expected != (item.revision if identity else 0):
            raise RentalConflict(
                "Content changed. Review the current version before saving.",
                code="stale_revision",
            )
        before = projection(kind, item) if identity else {}
        values = validated(kind, data["values"], item if identity else None)
        for name, value in values.items():
            setattr(item, name, value)
        item.revision = uuid.uuid4().hex if entry.opaque_revision else expected + 1
        try:
            item.full_clean()
        except ModelValidationError as exc:
            raise ValidationError(exc.message_dict)
        try:
            with transaction.atomic():
                item.save(force_insert=identity is None)
        except IntegrityError:
            raise RentalConflict(
                "This content identity already exists. Review its current version."
            )
        commerce_benefit_editor.changed(parent_plan, item, user, data["reason"])
        result = projection(kind, item)
        audit_revision = item.revision
        if entry.opaque_revision:
            from django.db.models import Max

            latest = (
                ContentEditAudit.objects.filter(
                    kind=kind, object_id=result["id"]
                ).aggregate(value=Max("revision"))["value"]
                or 0
            )
            audit_revision = latest + 1
        ContentEditAudit.objects.create(
            kind=kind,
            object_id=result["id"],
            revision=audit_revision,
            actor=user,
            reason=data["reason"],
            before=before,
            after=result,
        )
        return result, 200 if identity else 201, None

    return execute_idempotent(
        user=user,
        operation=operation,
        key=key,
        payload=data,
        action=apply,
        auth_claims=auth_claims,
    )


@transaction.atomic
def recover(user, kind, identity, key, auth_claims=None):
    require_staff_actor(user, {"system_owner"})
    spec(kind)
    row = resolve_or_close(
        user=user,
        operation=operation_name(kind, identity),
        key=key,
        auth_claims=auth_claims,
    )
    # Recheck staff authority after the user lock, including receipt retrieval.
    require_staff_actor(user, {"system_owner"})
    return {
        "status": row.recovery_status,
        "receipt": row.response_data if row.recovery_status == "confirmed" else None,
    }
