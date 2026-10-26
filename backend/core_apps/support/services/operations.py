"""Shared support authority, one assignee, private notes and versioned transitions."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from core_apps.admin_api.permissions import require_staff_actor
from core_apps.admin_api.models import StaffProfile
from core_apps.common.idempotency import execute_idempotent, resolve_or_close
from core_apps.features.models import IdempotencyRecord
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.users.models import User
from core_apps.support.models import Ticket, TicketTransition, TicketInternalNote

SUPERVISORS = {"system_owner", "support_supervisor"}
SUPPORT = SUPERVISORS | {"support"}


def actor(user, *, write=False):
    return require_staff_actor(user, SUPPORT, lock=write)


def supervisor(user):
    return (
        user.is_superuser
        or StaffProfile.objects.filter(
            user=user, is_active=True, role_name__in=SUPERVISORS
        ).exists()
    )


def record_transition(ticket, user, action, reason, previous):
    TicketTransition.objects.create(
        ticket=ticket,
        actor=user,
        action=action,
        reason=reason,
        revision=ticket.revision,
        previous_assignee_id=previous,
        assignee=ticket.assigned_to,
    )


def require_independent(ticket, user):
    if ticket.user_id == user.pk:
        raise PermissionDenied("An independent operator must service this inquiry.")


def own_for_reply(ticket, user):
    require_independent(ticket, user)
    if ticket.escalated and not supervisor(user):
        raise PermissionDenied(
            "An escalated inquiry requires an authorized support supervisor."
        )
    if ticket.assigned_to_id and ticket.assigned_to_id != user.pk:
        raise PermissionDenied(
            "Only the assigned operator can reply. Request reassignment first."
        )
    if not ticket.assigned_to_id:
        ticket.assigned_to = user
        ticket.save(update_fields=["assigned_to", "updated_at"])
        # The reply advances the revision in the same transaction.
        TicketTransition.objects.create(
            ticket=ticket,
            actor=user,
            action="claim",
            reason="Assigned when replying.",
            revision=ticket.revision + 1,
            assignee=user,
        )


@transaction.atomic
def command(user, ticket_id, data, key):
    # Lock assignees in stable order before the ticket, matching staff reply writes.
    assignee_id = data.get("assignee_id")
    ids = [user.pk]
    if assignee_id:
        target = User.objects.filter(id=assignee_id).first()
        if not target:
            raise ValidationError({"assignee_id": "Choose a current support operator."})
        ids.append(target.pk)
    list(User.objects.select_for_update().filter(pk__in=ids).order_by("pk"))
    user = actor(user, write=True)
    ticket = Ticket.objects.select_for_update().filter(id=ticket_id).first()
    if not ticket:
        raise NotFound()
    require_independent(ticket, user)
    if not key:
        raise ValidationError(
            {"Idempotency-Key": "Retain an operation key for this command."}
        )

    def apply():
        if ticket.revision != data["expected_revision"]:
            raise RentalConflict("Review the current ticket.", code="stale_revision")
        action = data["action"]
        previous = ticket.assigned_to_id
        if action != "note" and ticket.status in {"resolved", "closed"}:
            raise RentalConflict("This inquiry is closed.")
        if action == "claim":
            if ticket.assigned_to_id:
                raise RentalConflict(
                    "Another operator already owns this ticket.",
                    code="already_assigned",
                )
            if ticket.escalated and not supervisor(user):
                raise PermissionDenied("Support supervisor authority is required.")
            ticket.assigned_to = user
            ticket.status = "in_progress"
        elif action == "assign":
            if not supervisor(user):
                raise PermissionDenied("Support supervisor authority is required.")
            target = actor(target_user(assignee_id), write=True)
            require_independent(ticket, target)
            if ticket.escalated and not supervisor(target):
                raise PermissionDenied(
                    "An escalated ticket must be assigned to a support supervisor."
                )
            ticket.assigned_to = target
            ticket.status = "in_progress"
        elif action == "escalate":
            if ticket.escalated:
                raise RentalConflict("This ticket is already in the supervisor queue.")
            if ticket.assigned_to_id not in {None, user.pk} and not supervisor(user):
                raise PermissionDenied(
                    "Only the responsible operator or supervisor can escalate."
                )
            ticket.escalated, ticket.assigned_to = True, None
            ticket.status = "in_progress"
        elif action == "note":
            TicketInternalNote.objects.create(
                ticket=ticket, actor=user, body=data["reason"]
            )
        else:
            raise ValidationError("Choose a supported support command.")
        ticket.revision += 1
        ticket.save(
            update_fields=[
                "assigned_to",
                "escalated",
                "status",
                "revision",
                "updated_at",
            ]
        )
        record_transition(ticket, user, action, data["reason"], previous)
        return (
            {
                "ticket_id": str(ticket.id),
                "revision": ticket.revision,
                "action": action,
            },
            200,
            ticket.id,
        )

    return execute_idempotent(
        user=user,
        operation=f"support.ticket.manage:{ticket.id}",
        key=key,
        payload=data,
        request_subject_id=ticket.id,
        action=apply,
    )


def target_user(identity):
    value = User.objects.filter(id=identity).first() if identity else None
    if not value:
        raise ValidationError({"assignee_id": "Choose a current support operator."})
    return value


def receipt(user, ticket_id, key, action, *, close=False, auth_claims=None):
    actor(user)
    if not Ticket.objects.filter(id=ticket_id).exists():
        raise NotFound()
    if action not in {"claim", "assign", "escalate", "note", "reply", "resolve"}:
        raise ValidationError("Choose the original support action.")
    operation = f"support.ticket.{'staff_' + action if action in {'reply', 'resolve'} else 'manage'}:{ticket_id}"
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


def projection(ticket, user, *, detail=False):
    assigned = ticket.assigned_to
    value = {
        "id": str(ticket.id),
        "rawId": str(ticket.id),
        "reference": ticket.reference,
        "subject": ticket.subject,
        "user": ticket.user.get_full_name or ticket.user.email,
        "userType": ticket.workspace,
        "workspace": ticket.workspace,
        "priority": "مصعّدة" if ticket.escalated else "عادية",
        "status": ticket.get_status_display(),
        "statusRaw": ticket.status,
        "created_at": ticket.created_at.isoformat(),
        "timeAgo": ticket.created_at.isoformat(),
        "revision": ticket.revision,
        "escalated": ticket.escalated,
        "assignedTo": (assigned.get_full_name or assigned.email) if assigned else None,
        "assigned_to_id": str(assigned.id) if assigned else None,
    }
    if not detail:
        return value
    from core_apps.support.serializers.ticket import TicketMessageSerializer
    from .staff_replies import can_resolve_inquiry

    independent = user.pk != ticket.user_id
    can_write = True
    try:
        from core_apps.users.services.totp import require_sensitive_access

        require_sensitive_access(user)
    except PermissionDenied:
        can_write = False
    responsible = independent and can_write and ticket.assigned_to_id in {None, user.pk}
    if ticket.escalated and not supervisor(user):
        responsible = False
    closed = ticket.status in {"closed", "resolved"}
    value.update(
        messages=TicketMessageSerializer(
            ticket.messages.order_by("created_at"), many=True
        ).data,
        rental_context=ticket.rental_context,
        internal_notes=[
            {
                "id": str(note.id),
                "body": note.body,
                "actor": note.actor.get_full_name or note.actor.email,
                "created_at": note.created_at.isoformat(),
            }
            for note in ticket.internal_notes.select_related("actor").order_by(
                "created_at"
            )
        ],
        transitions=[
            {
                "id": str(row.id),
                "action": row.action,
                "reason": row.reason,
                "revision": row.revision,
                "created_at": row.created_at.isoformat(),
                "actor": row.actor.get_full_name or row.actor.email,
                "assignee": (
                    (row.assignee.get_full_name or row.assignee.email)
                    if row.assignee
                    else None
                ),
            }
            for row in ticket.transitions.select_related("actor", "assignee").order_by(
                "created_at"
            )
        ],
        actions={
            "reply": responsible and not closed,
            "resolve": responsible and not closed and can_resolve_inquiry(ticket),
            "claim": responsible and not closed and not assigned,
            "assign": independent and can_write and supervisor(user) and not closed,
            "escalate": independent
            and can_write
            and not closed
            and not ticket.escalated
            and (ticket.assigned_to_id in {None, user.pk} or supervisor(user)),
            "note": independent and can_write,
        },
    )
    return value
