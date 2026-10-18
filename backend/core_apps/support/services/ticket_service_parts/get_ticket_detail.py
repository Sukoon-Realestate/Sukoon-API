"""Ticket service: get ticket detail."""

import uuid
from typing import Any, Optional
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.support.models import Ticket, TicketMessage
from .create_ticket import logger, TicketClosedConflict


def get_ticket_detail(
    user: Any, ticket_id: str, workspace: Optional[str] = None
) -> Ticket:
    """
    Retrieves full ticket detail ensuring account ownership and workspace scoping.
    Raises Ticket.DoesNotExist on ownership/workspace mismatch.
    """
    qs = (
        Ticket.objects.select_related("user")
        .prefetch_related("messages", "messages__attachments")
        .filter(user=user)
    )

    # Allow querying by UUID id or reference
    try:
        uuid_val = uuid.UUID(ticket_id)
        ticket = qs.filter(id=uuid_val).first()
    except (ValueError, AttributeError):
        ticket = qs.filter(reference=ticket_id).first()

    if not ticket:
        raise Ticket.DoesNotExist("Ticket not found or access denied.")

    if workspace:
        normalized_workspace = "owner" if workspace.lower() == "owner" else "tenant"
        if ticket.workspace != normalized_workspace:
            raise Ticket.DoesNotExist("Ticket does not belong to requested workspace.")

    return ticket


@transaction.atomic
def add_ticket_reply(
    user: Any, ticket_id: str, body: str, workspace: Optional[str] = None
) -> Ticket:
    """
    Adds a reply to an active ticket and returns the complete updated ticket.
    Rejects replies to resolved/closed tickets with TicketClosedConflict.
    """
    ticket = get_ticket_detail(user, ticket_id, workspace=workspace)
    ticket = Ticket.objects.select_for_update().get(pk=ticket.pk)

    if ticket.status in [Ticket.Status.RESOLVED, Ticket.Status.CLOSED]:
        raise TicketClosedConflict("لا يمكن الرد على تذكرة دعم تم حلها أو إغلاقها.")

    clean_body = body.strip()
    if len(clean_body) < 1 or len(clean_body) > 4000:
        raise ValidationError({"body": "يجب أن يتراوح طول نص الرد بين 1 و4000 حرف."})

    TicketMessage.objects.create(
        ticket=ticket,
        sender=TicketMessage.SenderType.USER,
        sender_user=user,
        body=clean_body,
    )

    ticket.updated_at = timezone.now()
    ticket.revision += 1
    ticket.save(update_fields=["revision", "updated_at"])

    logger.info("Added reply to ticket %s by user %s", ticket.reference, user.id)
    return get_ticket_detail(user, ticket_id, workspace=workspace)
