"""Private operational review of a report; never evidence of invoice settlement."""

from rest_framework.exceptions import ValidationError
from core_apps.features.models import Lease, RentalOperationalCase
from core_apps.features.planning_models import PlanningEvent
from core_apps.support.models import Ticket, TicketMessage

KIND = "off_platform_payment_report"


def open_report(ticket, lease_id):
    from core_apps.features.services.rental_lifecycle.cases import open_system_case

    # Do not copy the reporter's narrative or attachment URLs into a case/push.
    item = open_system_case(
        kind=KIND,
        source_key=f"support.payment:{ticket.id}",
        lease=Lease.objects.filter(pk=lease_id).first() if lease_id else None,
        actor=ticket.user,
        reason="Private report concerning payment outside Sokoun.",
        next_action=(
            "Assign an independent financial operator to review the linked support "
            "ticket. This report does not pay, refund or change any invoice."
        ),
    )
    item.baseline = {**item.baseline, "support_ticket_id": str(ticket.id)}
    item.save(update_fields=["baseline", "updated_at"])
    ticket.rental_context = {**ticket.rental_context, "case_id": str(item.id)}
    ticket.save(update_fields=["rental_context", "updated_at"])


def readable_tickets(user):
    # Django builds its available-app projection on the anonymous login page.
    # Never pass AnonymousUser (or an inactive identity) into an FK query.
    if not user or not getattr(user, "is_authenticated", False) or not user.is_active:
        return Ticket.objects.none()
    from .staff_replies import can_service_tickets
    from core_apps.features.services.rental_lifecycle.cases import (
        independent_case_operator,
    )

    if can_service_tickets(user):
        return Ticket.objects.all()
    cases = RentalOperationalCase.objects.filter(kind=KIND, assigned_to=user)
    identifiers = [
        item.baseline.get("support_ticket_id")
        for item in cases.select_related("lease", "assigned_to")
        if independent_case_operator(item, user)
    ]
    return Ticket.objects.filter(id__in=[value for value in identifiers if value])


def can_read_ticket(user, ticket):
    return readable_tickets(user).filter(pk=ticket.pk).exists()


def validate_action(item, data):
    if item.kind != KIND:
        return
    if data.get("action") == "link_remedy":
        raise ValidationError(
            "An off-platform report cannot establish platform custody or a refund. "
            "Use the original payment's authorized remedy workflow when applicable."
        )
    if (
        data.get("action") == "resolve"
        and data.get("resolution_code") != "no_action_required"
    ):
        raise ValidationError(
            "Close only the report review using no_action_required and explain the "
            "outcome. This does not certify payment, refund or mutual settlement."
        )


def sync_review(item, actor, action):
    if item.kind != KIND or action not in {"resolve", "reopen", "request_review"}:
        return
    ticket = (
        Ticket.objects.select_for_update()
        .filter(id=item.baseline.get("support_ticket_id"))
        .first()
    )
    if not ticket:
        return
    ticket.status = (
        Ticket.Status.RESOLVED
        if item.status == "resolved"
        else Ticket.Status.IN_PROGRESS
    )
    ticket.revision += 1
    ticket.save(update_fields=["status", "revision", "updated_at"])
    body = (
        "اكتملت مراجعة البلاغ. هذا لا يسدد أو يسترد أو يغيّر الفاتورة. راجع نتيجة المتابعة. / "
        "Report review completed. This does not pay, refund or change the invoice. Review the case outcome."
        if item.status == "resolved"
        else "أعيد فتح متابعة البلاغ. / Report review reopened."
    )
    message = TicketMessage.objects.create(
        ticket=ticket, sender="support", sender_user=actor, body=body
    )
    PlanningEvent.objects.get_or_create(
        recipient=ticket.user,
        event_key=f"support.payment_review:{message.id}",
        defaults={
            "destination": {
                "action_type": "open_support_ticket",
                "target_id": str(ticket.id),
                "workspace": ticket.workspace,
                "schema_version": "1",
            }
        },
    )
