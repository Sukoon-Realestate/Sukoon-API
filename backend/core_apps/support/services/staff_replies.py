"""An operator reply is advice, never a financial or possession decision."""

from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from core_apps.common.idempotency import execute_idempotent
from core_apps.features.models import RentalAuditEvent
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.rental_lifecycle.common import staff_role
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.support.models import Ticket, TicketMessage


def can_service_tickets(user):
    return staff_role(user, {"support"})


def can_resolve_inquiry(ticket):
    """General advice has no authority to settle linked or protected cases."""
    return (
        ticket.category == Ticket.Category.OTHER
        and not ticket.rental_context
        and not ticket.reference.startswith("PRIVACY-")
    )


@transaction.atomic
def reply_as_staff(
    *,
    user,
    ticket_id,
    body,
    expected_revision,
    request_key,
    resolve_inquiry=False,
    acknowledge_resolution=False,
    attachment_ids=None,
):
    from core_apps.users.models import User
    from core_apps.admin_api.models import StaffProfile

    user = User.objects.select_for_update().get(pk=user.pk)
    StaffProfile.objects.select_for_update().filter(user=user).first()
    if not can_service_tickets(user):
        raise PermissionDenied("An active support operator is required.")
    ticket = Ticket.objects.select_for_update().filter(id=ticket_id).first()
    if not ticket:
        raise NotFound()
    if ticket.user_id == user.pk:
        raise PermissionDenied("An independent operator must service this inquiry.")
    clean = body.strip()
    if (
        (not clean and not attachment_ids)
        or len(clean) > 4000
        or not request_key
        or len(request_key) > 100
    ):
        raise ValidationError("Supply the reply and its original operation key.")
    if resolve_inquiry and acknowledge_resolution is not True:
        raise ValidationError("Acknowledge that only the general inquiry is resolved.")
    action = "resolve" if resolve_inquiry else "reply"

    def apply():
        if type(expected_revision) is not int or expected_revision != ticket.revision:
            raise RentalConflict("Review the current ticket.", code="stale_revision")
        if ticket.status in {Ticket.Status.CLOSED, Ticket.Status.RESOLVED}:
            raise RentalConflict("This inquiry is closed.")
        if resolve_inquiry and not can_resolve_inquiry(ticket):
            raise RentalConflict(
                "Linked rental, verification and retention cases require their domain "
                "resolution. Only an unlinked general inquiry can be resolved here.",
                code="domain_resolution_required",
            )
        message = TicketMessage.objects.create(
            ticket=ticket,
            sender="support",
            sender_user=user,
            body=clean,
        )
        from core_apps.support.services.staged_attachments import bind

        bind(message, attachment_ids or [], user=user)
        ticket.revision += 1
        ticket.status = (
            Ticket.Status.RESOLVED if resolve_inquiry else Ticket.Status.IN_PROGRESS
        )
        ticket.save(update_fields=["revision", "status", "updated_at"])
        PlanningEvent.objects.get_or_create(
            recipient=ticket.user,
            event_key=f"support.{action}:{message.id}",
            defaults={
                "destination": {
                    "action_type": "open_support_ticket",
                    "target_id": str(ticket.id),
                    "workspace": ticket.workspace,
                    "schema_version": "1",
                }
            },
        )
        RentalAuditEvent.objects.create(
            actor=user,
            subject_kind="support_ticket",
            subject_id=ticket.id,
            subject_revision=ticket.revision,
            action=f"support.{action}",
            reason=(
                "General inquiry resolved; no domain remedy executed."
                if resolve_inquiry
                else "Advice-only reply; no domain remedy executed."
            ),
            metadata={"message_id": str(message.id)},
        )
        return (
            {
                "ticket_id": str(ticket.id),
                "message_id": str(message.id),
                "revision": ticket.revision,
                "effect": "inquiry_resolved" if resolve_inquiry else "advice_only",
            },
            200,
            message.id,
        )

    payload = {"body": clean, "expected_revision": expected_revision}
    if attachment_ids:
        payload["attachment_ids"] = [str(identity) for identity in attachment_ids]
    if resolve_inquiry:
        payload["acknowledge_resolution"] = acknowledge_resolution
    return execute_idempotent(
        user=user,
        operation=f"support.ticket.staff_{action}:{ticket.id}",
        key=request_key,
        payload=payload,
        request_subject_id=ticket.id,
        action=apply,
    )
