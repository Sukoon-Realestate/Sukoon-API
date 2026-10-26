"""Version-bound moderation shared by API, dashboard deployments and Django admin."""

import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.admin_api.permissions import require_staff_actor
from core_apps.common.idempotency import execute_idempotent, fingerprint
from core_apps.features.models import RentalAuditEvent
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.rental_phase2 import RentalConflict
from ..models import Property, PropertyModerationDecision


def capabilities(prop, reviewer):
    reason = ""
    try:
        current = require_staff_actor(
            reviewer, {"system_owner", "main_admin", "property_reviewer"}
        )
        from core_apps.users.services.totp import require_sensitive_access

        require_sensitive_access(current)
        if current.pk == prop.owner_id:
            reason = "يلزم مراجع مستقل عن المالك."
        elif prop.retired_at:
            reason = "هذه الوحدة مؤرشفة. راجع سجل المخزون."
    except PermissionDenied:
        reason = "الإجراءات متوقفة؛ راجع صلاحياتك وأمان الحساب."
    values = {}
    for action in ("approve", "reject", "request_revision", "block", "unblock"):
        why = reason
        if not why and prop.moderation_blocked and action != "unblock":
            why = "يلزم رفع الحظر أولًا."
        elif not why and action == "unblock" and not prop.moderation_blocked:
            why = "لا يوجد حظر إداري على العقار."
        elif (
            not why
            and action == "approve"
            and prop.status not in {Property.Status.UNDER_REVIEW}
        ):
            why = "يلزم تقديم العقار للمراجعة أولًا."
        values[action] = {"enabled": not why, "reason": why}
    return values


def receipt(user, property_id, key, *, close=False, auth_claims=None):
    from core_apps.common.idempotency import resolve_or_close
    from core_apps.features.models import IdempotencyRecord
    from django.shortcuts import get_object_or_404

    require_staff_actor(user, {"system_owner", "main_admin", "property_reviewer"})
    prop = get_object_or_404(Property, id=property_id)
    operation = f"property.moderate:{prop.id}"
    row = (
        resolve_or_close(
            user=user, operation=operation, key=key, auth_claims=auth_claims
        )
        if close
        else (
            IdempotencyRecord.objects.filter(
                user=user, request_key=key, operation=operation
            ).first()
        )
    )
    return (
        {"status": row.recovery_status, "receipt": row.response_data}
        if row
        else {"status": "unknown"}
    )


def snapshot(prop):
    excluded = {
        "pkid",
        "created_at",
        "updated_at",
        "search_document",
        "availability_confirmed_at",
    }
    data = {}
    for field in Property._meta.concrete_fields:
        if field.name in excluded:
            continue
        value = getattr(prop, field.attname)
        if field.__class__.__name__ == "CloudinaryField":
            value = str(value) if value else None
        data[field.name] = value
    data["images"] = [
        {
            "id": str(image.id),
            "file": str(image.image),
            "name": image.name,
            "description": image.description,
            "position": image.position,
        }
        for image in prop.images.order_by("position", "id")
    ]
    # IDs remain stable when a catalog's display translation changes.
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


def version(prop):
    return fingerprint(snapshot(prop))


def history(prop, *, internal=False):
    return [
        {
            "id": str(item.id),
            "revision": item.source_revision,
            "version": item.source_version,
            "action": item.action,
            "reason": item.public_reason,
            "created_at": item.created_at.isoformat(),
            **(
                {"internal_note": item.internal_note, "reviewer": str(item.reviewer.id)}
                if internal
                else {}
            ),
        }
        for item in prop.moderation_decisions.select_related("reviewer").order_by(
            "created_at"
        )
    ]


@transaction.atomic
def decide(
    property_id,
    *,
    reviewer,
    action,
    expected_version,
    request_key,
    reason="",
    internal_note="",
):
    reviewer = require_staff_actor(
        reviewer, {"system_owner", "main_admin", "property_reviewer"}, lock=True
    )
    from core_apps.admin_api.services.property_service_parts.get_admin_properties_queryset import (
        _get_property_by_identifier,
    )

    found = _get_property_by_identifier(property_id)
    prop = Property.objects.select_for_update().get(pk=found.pk)
    if prop.owner_id == reviewer.pk:
        raise PermissionDenied("A listing requires independent moderation.")
    if action not in {"approve", "reject", "request_revision", "block", "unblock"}:
        raise ValidationError("Choose a supported moderation action.")
    if not expected_version or not request_key:
        raise ValidationError(
            "Review the current listing and retain its version and operation key."
        )
    reason, internal_note = reason.strip(), internal_note.strip()
    if action != "approve" and not reason:
        raise ValidationError({"reason": "Explain the decision to the owner."})
    if len(reason) > 2000 or len(internal_note) > 4000:
        raise ValidationError("The review note is too long.")

    def apply():
        observed = snapshot(prop)
        if fingerprint(observed) != expected_version:
            raise RentalConflict(
                "The listing or evidence changed. Review its current version.",
                code="review_version_changed",
            )
        if prop.retired_at:
            raise RentalConflict(
                "Retired inventory cannot be republished.", code="inventory_retired"
            )
        if prop.moderation_blocked and action != "unblock":
            raise RentalConflict(
                "Lift the independent moderation block before reviewing this listing.",
                code="property_blocked",
            )
        if action == "unblock" and not prop.moderation_blocked:
            raise RentalConflict("This listing is not blocked.")
        if action == "approve" and prop.status not in {Property.Status.UNDER_REVIEW}:
            raise RentalConflict("The owner must submit this listing for review first.")
        before = prop.status
        item = PropertyModerationDecision.objects.create(
            property=prop,
            reviewer=reviewer,
            source_revision=prop.review_revision,
            source_version=expected_version,
            snapshot=observed,
            action=action,
            public_reason=reason,
            internal_note=internal_note,
        )
        prop.is_verified = action == "approve"
        prop.moderation_reason = reason
        if action == "approve":
            prop.status = Property.Status.VERIFIED
        elif action in {"reject", "request_revision"}:
            prop.status = Property.Status.NEEDS_REVISION
        elif action == "block":
            prop.moderation_blocked = True
            prop.status = Property.Status.HIDDEN
        else:
            prop.moderation_blocked = False
            prop.status = Property.Status.UNDER_REVIEW
        prop.review_revision += 1
        prop.save(
            update_fields=[
                "status",
                "is_verified",
                "review_revision",
                "moderation_reason",
                "moderation_blocked",
                "updated_at",
            ]
        )
        RentalAuditEvent.objects.create(
            actor=reviewer,
            subject_kind="property",
            subject_id=prop.id,
            subject_revision=item.source_revision,
            action=f"property.moderation.{action}",
            reason=reason,
            metadata={
                "decision_id": str(item.id),
                "version": expected_version,
                "before": before,
                "after": prop.status,
            },
        )
        PlanningEvent.objects.create(
            recipient=prop.owner,
            event_key=f"property.moderation:{item.id}",
            destination={
                "action_type": "view_property",
                "property_id": str(prop.id),
                "target_id": str(prop.id),
                "workspace": "owner",
                "revision": prop.review_revision,
                "event_kind": "property_review_changed",
                "schema_version": "1",
            },
        )
        return (
            {
                "property_id": str(prop.id),
                "decision_id": str(item.id),
                "revision": prop.review_revision,
                "status": prop.status,
                "version": version(prop),
            },
            200,
            item.id,
        )

    return execute_idempotent(
        user=reviewer,
        operation=f"property.moderate:{prop.id}",
        key=request_key,
        payload={
            "action": action,
            "expected_version": expected_version,
            "reason": reason,
            "internal_note": internal_note,
        },
        request_subject_id=prop.id,
        action=apply,
    )
