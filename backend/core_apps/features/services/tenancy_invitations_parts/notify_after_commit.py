"""Save invitation receipts with their transaction; the durable worker sends Push."""

from core_apps.features.models import TenancyInvitation
from core_apps.notifications.models import Notification
from core_apps.notifications.services.notification_service import NotificationService
from .validate_accounts import localized


def notify_after_commit(
    *, recipient, invitation, notification_type, title, body, label
):
    workspace = recipient_scope(invitation, recipient.pk)
    data = {
        "workspace": workspace,
        "revision": invitation.revision,
        "schema_version": "1",
        "action_label": label,
        "action_type": "open_tenancy_invitation",
        "target_id": str(invitation.id),
    }
    if invitation.source_visit_id:
        data["source_visit_id"] = str(invitation.source_visit.id)
    if invitation.source_decision_id:
        data["source_decision_id"] = str(invitation.source_decision.id)
    notification = NotificationService.create_notification(
        user=recipient,
        title=title,
        body=body,
        notification_type=notification_type,
        category="tenancy_invitation",
        icon_type="contract",
        data=data,
        send_push=True,
    )

    return notification


def recipient_scope(invitation, recipient_id):
    if recipient_id == invitation.owner_id:
        return "owner"
    if invitation.source_visit_id:
        from core_apps.properties.services.viewing_notifications import (
            recipient_scope as visit_scope,
        )

        return visit_scope(invitation.source_visit, recipient_id)
    return "individual"


def notice_allowed(notification):
    from django.core.exceptions import ValidationError

    data = notification.data or {}
    try:
        invitation = TenancyInvitation.objects.filter(id=data.get("target_id")).first()
    except (ValueError, TypeError, ValidationError):
        return False
    # A previous revision is history, not authority. Check the exact subject and
    # recipient again on every device attempt, without replaying any domain action.
    return bool(
        invitation
        and notification.user_id in {invitation.owner_id, invitation.tenant_id}
        and notification.scope == recipient_scope(invitation, notification.user_id)
    )


def create_notification_for_invitation(request, invitation):
    notify_after_commit(
        recipient=invitation.tenant,
        invitation=invitation,
        notification_type=Notification.NotificationType.TENANCY_INVITATION,
        title=localized(request, "Rental invitation", "دعوة للإيجار"),
        body=localized(
            request,
            "Review the invitation to proceed with a lease.",
            "راجع الدعوة للمتابعة إلى عقد الإيجار.",
        ),
        label=localized(request, "Review invitation", "مراجعة الدعوة"),
    )


def create_notification_for_response(request, invitation):
    accepted = invitation.status == TenancyInvitation.Status.ACCEPTED
    notify_after_commit(
        recipient=invitation.owner,
        invitation=invitation,
        notification_type=Notification.NotificationType.TENANCY_INVITATION_RESPONSE,
        title=localized(request, "Invitation response", "الرد على دعوة الإيجار"),
        body=localized(
            request,
            (
                "The tenant accepted your rental invitation."
                if accepted
                else "The tenant rejected your rental invitation."
            ),
            (
                "وافق المستأجر على دعوة الإيجار."
                if accepted
                else "رفض المستأجر دعوة الإيجار."
            ),
        ),
        label=localized(request, "Review invitation", "مراجعة الدعوة"),
    )
