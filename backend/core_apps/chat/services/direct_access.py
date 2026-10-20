"""Direct participants share media/receipts without acquiring group authority."""

import uuid
from dataclasses import dataclass
from django.db import transaction
from django.db.models import Max
from rest_framework.exceptions import PermissionDenied
from core_apps.chat.models import Conversation, ConversationParticipant
from core_apps.users.models import User
from .message_service_parts.get_or_create_direct_conversation import (
    direct_message_blocked,
)


@dataclass(frozen=True)
class DirectConversationGrant:
    id: object
    role: str = "member"
    can_send: bool = False


def lock_root(conversation):
    # Match direct conversation creation: users, relationship, conversation.
    people = list(
        User.objects.select_for_update()
        .filter(
            conversation_participants__conversation=conversation,
        )
        .order_by("pk")
    )
    if len(people) == 2:
        direct_message_blocked(people[0], people[1], lock=True)
    return Conversation.objects.select_for_update().get(pk=conversation.pk)


def prepare_locked(conversation):
    """Upgrade old text history under the same lock used by every new send.

    No messages or unread counts are invented; original IDs/timestamps remain.
    Old clients may still send text after a new client opens the conversation.
    """
    highest = conversation.messages.aggregate(value=Max("sequence"))["value"] or 0
    for message in conversation.messages.filter(sequence__isnull=True).order_by(
        "created_at", "pk"
    ):
        highest += 1
        message.sequence = highest
        message.save(update_fields=["sequence"])
    if conversation.last_sequence != highest:
        conversation.last_sequence = highest
        conversation.save(update_fields=["last_sequence"])
    for participant in conversation.participant_set.filter(
        membership_period__isnull=True
    ):
        participant.membership_period = uuid.uuid4()
        if participant.last_read_at:
            participant.last_read_sequence = (
                conversation.messages.filter(
                    created_at__lte=participant.last_read_at,
                ).aggregate(value=Max("sequence"))["value"]
                or 0
            )
        participant.save(update_fields=["membership_period", "last_read_sequence"])
    return conversation


def authorize(conversation, user, *, action="read_chat", lock=False):
    fresh = User.objects.get(pk=user.pk)
    if (
        conversation.kind != "direct"
        or not fresh.is_active
        or not ConversationParticipant.objects.filter(
            conversation=conversation, user=fresh
        ).exists()
    ):
        raise PermissionDenied(
            "Conversation access is unavailable.", code="chat_access_revoked"
        )
    if lock:
        conversation = prepare_locked(lock_root(conversation))
        fresh.refresh_from_db(fields=["is_active"])
    elif conversation.participant_set.filter(membership_period__isnull=True).exists():
        with transaction.atomic():
            conversation = prepare_locked(lock_root(conversation))
    participant = ConversationParticipant.objects.filter(
        conversation=conversation, user=fresh
    ).first()
    if conversation.kind != "direct" or not fresh.is_active or participant is None:
        raise PermissionDenied(
            "Conversation access is unavailable.", code="chat_access_revoked"
        )
    others = list(conversation.participants.exclude(pk=fresh.pk))
    can_send = (
        len(others) == 1
        and others[0].is_active
        and not direct_message_blocked(fresh, others[0], lock=lock)
    )
    grant = DirectConversationGrant(participant.id, can_send=can_send)
    if action not in actions(grant):
        raise PermissionDenied("Messaging consent is not active for this conversation.")
    return conversation, participant, grant


def actions(grant):
    # Historical reading is retained when a roommate connection is withdrawn.
    result = [
        "read_chat",
        "mark_read",
        "set_notification_preference",
        "delete_own_message",
    ]
    if grant.can_send:
        result += ["send_message", "upload_attachment", "reply"]
    return result


def eligible_participants(conversation):
    return conversation.participant_set.filter(user__is_active=True)
