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
    # Match direct creation order. NO KEY UPDATE also lets ordinary group
    # messages reference these users while a multi-chat forward waits on a group.
    people = list(
        User.objects.select_for_update(no_key=True)
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
    from core_apps.chat.moderation.policy import (
        attach_context,
        require_send,
        restricted,
        mode,
    )

    if mode() != "off":
        attach_context(conversation, fresh)
    if action in {"send_message", "upload_attachment", "reply"}:
        require_send(conversation, fresh)
    can_send = can_send and not restricted(fresh)
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


def authorize_page(conversations, user):
    """Current direct-read grants for one bounded page; never mutation authority.

    The read-only path has no policy enrollment side effects. Moderation-enabled
    reads retain authorize() so its enrollment boundary continues to execute.
    """
    from collections import defaultdict
    from django.db.models import Q
    from rest_framework.exceptions import PermissionDenied
    from core_apps.chat.models import ChatBlock, AccountRestriction
    from core_apps.chat.moderation.policy import ACTIVE_RESTRICTIONS, mode
    from core_apps.features.planning_models import RoommateConnection

    if mode() != "off":
        return {}
    fresh = User.objects.get(pk=user.pk)
    if not fresh.is_active:
        raise PermissionDenied(
            "Conversation access is unavailable.", code="chat_access_revoked"
        )
    ids = [
        conversation.pk
        for conversation in conversations
        if conversation.kind == "direct"
    ]
    current = {
        row.pk: row for row in Conversation.objects.filter(pk__in=ids, kind="direct")
    }
    rosters = defaultdict(list)
    for participant in ConversationParticipant.objects.filter(
        conversation_id__in=ids
    ).select_related("user__profile"):
        rosters[participant.conversation_id].append(participant)
    peers = {
        row.user_id
        for roster in rosters.values()
        for row in roster
        if row.user_id != fresh.pk
    }
    blocks = list(
        ChatBlock.objects.filter(
            Q(user=fresh, blocked_user_id__in=peers)
            | Q(blocked_user=fresh, user_id__in=peers)
        ).values_list("user_id", "blocked_user_id")
    )
    own_blocks = {other for actor, other in blocks if actor == fresh.pk}
    blocked = {other if actor == fresh.pk else actor for actor, other in blocks}
    withdrawn = set(
        RoommateConnection.objects.filter(
            Q(first_id=fresh.pk, second_id__in=peers)
            | Q(second_id=fresh.pk, first_id__in=peers)
        )
        .exclude(status="accepted")
        .values_list("first_id", "second_id")
    )
    restricted = AccountRestriction.objects.filter(
        user=fresh, state__in=ACTIVE_RESTRICTIONS
    ).exists()
    result = {}
    for conversation in conversations:
        if conversation.kind != "direct":
            continue
        current_conversation = current.get(conversation.pk)
        roster = rosters[conversation.pk]
        participant = next((row for row in roster if row.user_id == fresh.pk), None)
        if not current_conversation or not participant:
            raise PermissionDenied(
                "Conversation access is unavailable.", code="chat_access_revoked"
            )
        if any(row.membership_period is None for row in roster):
            # Legacy sequence/membership preparation keeps its existing locks.
            continue
        others = [row.user for row in roster if row.user_id != fresh.pk]
        can_send = (
            len(others) == 1
            and others[0].is_active
            and not restricted
            and others[0].pk not in blocked
            and tuple(sorted([fresh.pk, others[0].pk])) not in withdrawn
        )
        grant = DirectConversationGrant(participant.id, can_send=can_send)
        result[conversation.pk] = {
            "authorized": (current_conversation, participant, grant),
            "roster": roster,
            "blocked_by_me": bool(others and others[0].pk in own_blocks),
            "is_blocked": bool(others and others[0].pk in blocked),
        }
    return result
