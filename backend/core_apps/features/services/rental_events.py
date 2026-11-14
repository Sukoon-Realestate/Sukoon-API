"""Rental timeline and notification dispatch shared by confirmed transitions."""

from ..models import RentalTimelineEvent, TenancyInvitation
from core_apps.notifications.services.notification_service import NotificationService


def _event(lease, actor, kind, label, resource_id=None, description=""):
    RentalTimelineEvent.objects.create(
        lease=lease,
        actor=actor,
        kind=kind,
        label=label,
        description=description,
        resource_id=resource_id or lease.id,
    )


def _notify(user, notification_type, title, action_type, target_id, **context):
    payload = {
        "action_type": action_type,
        "target_id": str(target_id),
        **{key: str(value) for (key, value) in context.items() if value is not None},
    }
    if context.get("lease_id"):
        invitation = (
            TenancyInvitation.objects.filter(lease__id=context["lease_id"])
            .select_related("source_visit", "source_decision")
            .first()
        )
        if invitation and invitation.source_visit_id:
            payload["source_visit_id"] = str(invitation.source_visit.id)
            payload["source_decision_id"] = str(invitation.source_decision.id)
    NotificationService.create_notification(
        user=user, notification_type=notification_type, title=title, data=payload
    )


__all__ = ["_event", "_notify"]
