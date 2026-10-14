"""Transactional event log with resumable fanout, independent of message cursors."""

import logging
from django.db import transaction
from rest_framework.exceptions import APIException
from core_apps.chat.models import ChatEvent
from .group_access import authorize
from .group_cursors import encode_cursor
from .group_projection import message_payload, summary

logger = logging.getLogger(__name__)


def record_event(conversation, kind, *, message=None, actor=None, data=None):
    conversation.last_event_sequence += 1
    conversation.save(update_fields=["last_event_sequence", "updated_at"])
    event = ChatEvent.objects.create(
        conversation=conversation,
        sequence=conversation.last_event_sequence,
        kind=kind,
        message=message,
        actor=actor,
        data=data or {},
    )
    transaction.on_commit(_wake_worker)
    return event


def _wake_worker():
    from django.conf import settings

    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        return
    try:
        from core_apps.chat.tasks import drain_chat_outbox

        drain_chat_outbox.delay()
    except Exception:
        # The committed log remains pending; the periodic worker will retry.
        logger.warning("Chat fanout wakeup failed; event remains queued.")


def event_payload(event, user):
    try:
        conversation, participant, member = authorize(event.conversation, user)
    except APIException:
        if event.kind == "conversation.access_revoked" and event.data.get(
            "user_id"
        ) == str(user.id):
            return {
                "type": event.kind,
                "payload": {"conversation_id": str(event.conversation.id)},
            }
        return None
    if event.kind == "conversation.access_revoked":
        return None
    payload = {
        "conversation_id": str(conversation.id),
        "event_id": str(event.id),
        "event_sequence": event.sequence,
        "event_cursor": encode_cursor(
            conversation, participant, "events", event.sequence
        ),
    }
    if event.message:
        if event.message.sequence < participant.visible_from_sequence:
            return None
        payload.update(message_payload(event.message, participant, member))
    elif event.kind == "conversation.updated":
        payload["conversation"] = summary(conversation, user)
    elif event.kind == "message.read":
        # No disclosure of a cursor or identity from a former membership period.
        from .group_access import eligible_participants

        reader = (
            eligible_participants(conversation)
            .filter(
                user=event.actor, membership_period=event.data.get("membership_period")
            )
            .first()
        )
        if not reader or reader.last_read_sequence < participant.visible_from_sequence:
            return None
        payload.update(
            {
                "reader_id": str(event.actor.id),
                "last_read_sequence": reader.last_read_sequence,
                "visible_from_sequence": reader.visible_from_sequence,
            }
        )
    return {"type": event.kind, "payload": payload}
