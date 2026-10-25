"""Revision-aware representative changes; never allocate rental inventory or money."""

from datetime import datetime
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.features.company_models import CompanyMembership
from core_apps.features.models import IdempotencyRecord
from core_apps.features.services.rental_lifecycle.common import audit, require_revision
from core_apps.features.services.rental_phase2 import RentalConflict
from ..models import Property, PropertyVisit
from .viewing_access import participant, can_read, group_process


def notify(visit, action, existing_notification=None):
    from core_apps.features.planning_models import PlanningEvent

    recipients = {visit.property.owner_id, visit.tenant_id}
    process = group_process(visit)
    if process:
        recipients.update(
            process.group.memberships.filter(
                user__id__in=process.consented_ids, status="active"
            ).values_list("user_id", flat=True)
        )
    for recipient in recipients:
        event, _ = PlanningEvent.objects.get_or_create(
            event_key=f"viewing:{visit.id}:{visit.revision}:{action}:{recipient}",
            defaults={
                "recipient_id": recipient,
                "destination": {
                    "action_type": "view_visit",
                    "event_kind": "viewing_changed",
                    "target_id": str(visit.id),
                    "visit_id": str(visit.id),
                    "workspace": (
                        "owner" if recipient == visit.property.owner_id else "tenant"
                    ),
                    "revision": visit.revision,
                    "change": action,
                },
            },
        )
        if (
            existing_notification
            and existing_notification.user_id == recipient
            and event.notification_id is None
        ):
            event.notification = existing_notification
            event.save(update_fields=["notification", "updated_at"])


@transaction.atomic
def command(actor, identity, data):
    found = get_object_or_404(PropertyVisit, id=identity)
    # Same property locking order as the canonical booking engine.
    Property.objects.select_for_update().get(pk=found.property_id)
    visit = (
        PropertyVisit.objects.select_for_update()
        .select_related("property", "property__owner", "tenant")
        .get(pk=found.pk)
    )
    if not can_read(visit, actor):
        raise PermissionDenied()
    require_revision(visit, data["expected_revision"])
    if visit.participant_decisions.exists() or visit.rental_invitations.exists():
        raise RentalConflict(
            "This viewing already has an attendance decision or commitment.",
            code="continuation_exists",
        )
    if visit.status not in {"pending", "confirmed"}:
        raise RentalConflict("This viewing is no longer open.", code="visit_not_open")
    action = data["action"]
    if action == "reassign":
        if (
            not visit.company_id
            or not CompanyMembership.objects.filter(
                company_id=visit.company_id,
                user=actor,
                is_active=True,
                is_coordinator=True,
            ).exists()
        ):
            raise PermissionDenied(
                "Only the current company coordinator can assign a representative."
            )
        membership = get_object_or_404(
            CompanyMembership.objects.select_for_update().select_related("user"),
            company_id=visit.company_id,
            id=data["representative_membership_id"],
            is_active=True,
            user__is_active=True,
        )
        old_attendee = str(visit.tenant.id)
        visit.tenant = membership.user
        visit.save(update_fields=["tenant", "updated_at"])
        audit(
            visit,
            actor,
            "viewing_representative_reassigned",
            metadata={
                "previous_attendee_id": old_attendee,
                "attendee_id": str(visit.tenant.id),
            },
        )
    else:
        raise ValidationError({"action": "Unsupported viewing action."})
    notify(visit, action)
    return visit
