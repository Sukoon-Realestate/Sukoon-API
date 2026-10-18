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


@transaction.atomic
def reply_as_staff(*, user, ticket_id, body, expected_revision, request_key):
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
    if not 1 <= len(clean) <= 4000 or not request_key or len(request_key) > 100:
        raise ValidationError("Supply the reply and its original operation key.")

    def apply():
        if type(expected_revision) is not int or expected_revision != ticket.revision:
            raise RentalConflict("Review the current ticket.", code="stale_revision")
        if ticket.status in {Ticket.Status.CLOSED, Ticket.Status.RESOLVED}:
            raise RentalConflict("This inquiry is closed.")
        message = TicketMessage.objects.create(
            ticket=ticket,
            sender="support",
            sender_user=user,
            body=clean,
        )
        ticket.revision += 1
        ticket.status = Ticket.Status.IN_PROGRESS
        ticket.save(update_fields=["revision", "status", "updated_at"])
        PlanningEvent.objects.get_or_create(
            recipient=ticket.user,
            event_key=f"support.reply:{message.id}",
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
            action="support.reply",
            reason="Advice-only reply; no domain remedy executed.",
            metadata={"message_id": str(message.id)},
        )
        return (
            {
                "ticket_id": str(ticket.id),
                "message_id": str(message.id),
                "revision": ticket.revision,
                "effect": "advice_only",
            },
            200,
            message.id,
        )

    return execute_idempotent(
        user=user,
        operation=f"support.ticket.staff_reply:{ticket.id}",
        key=request_key,
        payload={"body": clean, "expected_revision": expected_revision},
        request_subject_id=ticket.id,
        action=apply,
    )
