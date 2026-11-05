"""Structured requests are inquiry follow-up, never a domain decision."""
from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from core_apps.common.idempotency import execute_idempotent, IdempotencyConflict
from core_apps.features.planning_models import PlanningEvent
from core_apps.support.models import Ticket, TicketMessage, TicketInformationRequest, TicketInformationEvent
from . import operations

ACTIONS = {"request_information", "accept_information", "return_information", "withdraw_information", "request_evidence", "mark_evidence_conflicting"}


def eligible(ticket):
    return ticket.workspace in {"account", "tenant", "owner"} and ticket.category != "payment" and not set(ticket.rental_context or {}).difference({"property_id", "visit_id", "offer_id"})


def projection(ticket):
    from . import information_evidence
    if not eligible(ticket):
        return []
    return [{"id": str(row.id), "revision": row.revision, "prompt": row.prompt, "status": row.status,
        "evidence_requirement": row.evidence_requirement, "evidence_versions": information_evidence.projection(row),
        "source_message_id": str(row.source_message.id), "answer_message_id": str(row.answer.id) if row.answer else None,
        "can_answer": row.status == "requested" and ticket.status not in {"closed", "resolved"},
        "history": [{"id": str(event.id), "action": event.action, "revision": event.revision,
            "reason": event.reason, "answer_message_id": str(event.answer.id) if event.answer else None,
            "created_at": event.created_at.isoformat()} for event in row.history.select_related("answer").order_by("created_at", "pk")],
        } for row in ticket.information_requests.select_related("source_message", "answer").order_by("created_at", "pk")]


def event(row, actor, action, reason=""):
    entry = TicketInformationEvent.objects.create(request=row, actor=actor, action=action,
        revision=row.revision, reason=reason, answer=row.answer)
    if actor.pk != row.ticket.user_id:
        PlanningEvent.objects.get_or_create(recipient=row.ticket.user, event_key=f"support.information:{entry.id}",
            defaults={"destination": {"event_kind": "support_information_changed", "action_type": "open_support_ticket",
                "target_id": str(row.ticket.id), "workspace": row.ticket.workspace,
                **({"scope": "account"} if row.ticket.workspace == "account" else {}), "schema_version": "1"}})


@transaction.atomic
def staff_command(user, ticket_id, data, key):
    user = operations.actor(user, write=True)
    ticket = Ticket.objects.select_for_update().filter(id=ticket_id).first()
    if not ticket:
        raise NotFound()
    operations.require_independent(ticket, user)
    if not eligible(ticket):
        raise PermissionDenied("Structured requests are limited to active MVP support inquiries.")
    if not key:
        raise ValidationError("Retain an operation key for this command.")
    def apply():
        if ticket.revision != data["expected_revision"]:
            raise IdempotencyConflict("Review the current ticket before changing its requests.")
        if ticket.status in {"closed", "resolved"}:
            raise IdempotencyConflict("This inquiry is closed.")
        operations.own_for_reply(ticket, user)
        action = data["action"]
        if action in {"request_information", "request_evidence"}:
            prompt = data.get("prompt", "").strip()
            if not prompt:
                raise ValidationError({"prompt": "Describe the information needed."})
            source = TicketMessage.objects.create(ticket=ticket, sender="support", sender_user=user, body=prompt)
            from .information_evidence import requirement
            row = TicketInformationRequest.objects.create(ticket=ticket, source_message=source, prompt=prompt, created_by=user,
                evidence_requirement=requirement(ticket) if action == "request_evidence" else {})
        else:
            row = TicketInformationRequest.objects.select_for_update().filter(ticket=ticket, id=data.get("information_request_id")).first()
            if row is None:
                raise NotFound()
            if row.revision != data.get("information_revision"):
                raise IdempotencyConflict("Review the current information request.")
            if row.status == "withdrawn" or (action != "withdraw_information" and row.status != "answer_sent"):
                raise IdempotencyConflict("This information request cannot take that action.")
            from .information_evidence import review
            if action != "withdraw_information":
                review(row, user, action, data["reason"])
            row.status = {"accept_information": "accepted", "return_information": "requested", "withdraw_information": "withdrawn", "mark_evidence_conflicting": "requested"}[action]
            row.revision += 1
            row.save(update_fields=["revision", "status", "updated_at"])
        event(row, user, action, data["reason"])
        ticket.revision += 1
        ticket.status = "in_progress"
        ticket.save(update_fields=["revision", "status", "updated_at"])
        operations.record_transition(ticket, user, action, data["reason"], ticket.assigned_to_id)
        return {"ticket_id": str(ticket.id), "information_request_id": str(row.id), "revision": ticket.revision,
                "information_revision": row.revision, "status": row.status}, 200, str(row.id)
    return execute_idempotent(user=user, operation=f"support.ticket.manage:{ticket.id}", key=key, payload=data, action=apply)


@transaction.atomic
def answer(*, user, ticket_id, workspace, request_id, expected_revision, body, attachment_ids):
    from .ticket_service import get_ticket_detail, add_ticket_reply
    from core_apps.users.models import User
    current = User.objects.select_for_update().get(pk=user.pk)
    if not current.is_active or current.closed_at or current.security_epoch != user.security_epoch:
        raise PermissionDenied("Account authority changed.")
    ticket = get_ticket_detail(user, ticket_id, workspace)
    ticket = Ticket.objects.select_for_update().get(pk=ticket.pk)
    if not eligible(ticket):
        raise PermissionDenied("This support request is outside the MVP inquiry scope.")
    row = TicketInformationRequest.objects.select_for_update().filter(ticket=ticket, id=request_id).first()
    if row is None:
        raise NotFound()
    if row.revision != expected_revision or row.status != "requested":
        raise IdempotencyConflict("Review the current information request before answering.")
    from .information_evidence import validate_answer, record_submission
    validate_answer(row, attachment_ids, user)
    updated = add_ticket_reply(user, ticket_id, body, workspace, attachment_ids)
    row.answer = updated.messages.order_by("-created_at", "-pkid").first()
    row.status = "answer_sent"
    row.revision += 1
    row.save(update_fields=["answer", "status", "revision", "updated_at"])
    record_submission(row)
    event(row, user, "answer_sent")
    return get_ticket_detail(user, ticket_id, workspace)
