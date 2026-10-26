"""Current destinations for a changed student/group review, without new consent."""

from core_apps.users.models import User
from ..planning_models import PlanningEvent


def record_change(process, previous_status):
    recipients = process.group.memberships.filter(
        status="active",
        user__id__in=process.participant_ids,
        joined_revision__lte=process.access_group_revision,
        user__is_active=True,
    ).values_list("user_id", flat=True)
    destinations = {
        identity: {
            "action_type": "open_housing_group",
            "target_id": str(process.group.id),
            "workspace": "student",
        }
        for identity in recipients
    }
    if process.visit_id or previous_status in {
        "submitted",
        "under_review",
        "approved",
        "accepted",
        "approved_to_proceed",
        "changes_requested",
        "scheduled",
    }:
        destinations[process.property.owner_id] = {
            "action_type": (
                "view_visit" if process.visit_id else "open_group_applications"
            ),
            "target_id": str(process.visit.id if process.visit_id else process.id),
            "workspace": "owner",
        }
    for identity, destination in destinations.items():
        if not User.objects.filter(pk=identity, is_active=True).exists():
            continue
        PlanningEvent.objects.get_or_create(
            recipient_id=identity,
            event_key=f"group.process.changed:{process.id}:{process.revision}",
            defaults={
                "destination": {
                    **destination,
                    "event_kind": "group_process_changed",
                    "process_id": str(process.id),
                    "process_revision": process.revision,
                    "visit_id": str(process.visit.id) if process.visit_id else "",
                    "schema_version": "1",
                }
            },
        )


def authorize(event):
    from django.shortcuts import get_object_or_404
    from rest_framework.exceptions import NotFound
    from ..planning_models import GroupProcess

    process = get_object_or_404(GroupProcess, id=event.destination.get("process_id"))
    owner = event.recipient_id == process.property.owner_id
    if owner:
        target = str(process.visit.id if process.visit_id else process.id)
        action = "view_visit" if process.visit_id else "open_group_applications"
        scope = "owner"
    elif (
        str(event.recipient.id) in process.participant_ids
        and process.group.memberships.filter(
            user=event.recipient,
            status="active",
            joined_revision__lte=process.access_group_revision,
        ).exists()
    ):
        target, action, scope = str(process.group.id), "open_housing_group", "student"
    else:
        raise NotFound()
    if (
        event.destination.get("target_id"),
        event.destination.get("action_type"),
        event.destination.get("workspace"),
    ) != (target, action, scope):
        raise NotFound()
    return {
        "title": "تغيّر إجراء المجموعة / Group review updated",
        "body": "راجع الحالة الحالية وسبب التغيير في السجل. الالتزامات القائمة محفوظة. / Review the current state and change history. Existing commitments are preserved.",
    }
