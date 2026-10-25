"""Mention progress is separate from the chat's monotonic read cursor."""

from django.db import transaction
from django.utils import timezone
from core_apps.chat.models import MessageMention
from .group_access import authorize
from .group_limits import ChatConflict


def pending_mentions(conversation, participant):
    return MessageMention.objects.filter(
        message__conversation=conversation,
        message__sequence__gte=participant.visible_from_sequence,
        message__deleted_at__isnull=True,
        user_id=participant.user_id,
        membership_period=participant.membership_period,
        seen_at__isnull=True,
    )


def navigation_payload(conversation, participant):
    pending = pending_mentions(conversation, participant)
    next_message = pending.order_by("message__sequence").values_list("message__id", flat=True).first()
    return {
        "membership_period": str(participant.membership_period),
        "count": pending.count(),
        "next_message_id": str(next_message) if next_message else None,
    }


@transaction.atomic
def see_mention(conversation, user, message_id, period):
    from .group_events import record_event

    conversation, participant, _ = authorize(conversation, user, lock=True)
    if str(participant.membership_period) != str(period):
        raise ChatConflict("Refresh the current chat membership before retrying.")
    changed = pending_mentions(conversation, participant).filter(message__id=message_id).update(seen_at=timezone.now())
    if changed:
        record_event(
            conversation,
            "mentions.updated",
            actor=user,
            data={
                "user_id": str(user.id),
                "membership_period": str(participant.membership_period),
            },
        )
    return navigation_payload(conversation, participant)
