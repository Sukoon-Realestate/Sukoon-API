"""Tenancy invitations: notify after commit."""

from django.db import transaction
from core_apps.features.models import TenancyInvitation
from core_apps.notifications.models import Notification
from core_apps.notifications.services.fcm_service import FCMService
from core_apps.notifications.services.notification_service import NotificationService
from .validate_accounts import localized


def notify_after_commit(
    *, recipient, invitation, notification_type, title, body, workspace, label
):
    data = {
        "workspace": workspace,
        "action_label": label,
        "action_type": "open_tenancy_invitation",
        "target_id": str(invitation.id),
    }
    if invitation.source_visit_id:
        data["source_visit_id"] = str(invitation.source_visit.id)
        data["source_decision_id"] = str(invitation.source_decision.id)
    NotificationService.create_notification(
        user=recipient,
        title=title,
        body=body,
        notification_type=notification_type,
        category="tenancy_invitation",
        icon_type="contract",
        data=data,
        send_push=False,
    )
    transaction.on_commit(
        lambda: FCMService.send_push_to_user(
            user=recipient,
            title=title,
            body=body,
            data={
                **data,
                "notification_type": notification_type,
                "action_type": "open_tenancy_invitation",
                "target_id": str(invitation.id),
                "workspace": workspace,
                "title": title,
                "body": body,
                "action_label": label,
            },
            notification_type=notification_type,
        )
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
        workspace="tenant",
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
        workspace="owner",
        label=localized(request, "Review invitation", "مراجعة الدعوة"),
    )
