"""Current membership, never the cached participant row, grants access."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from core_apps.features.planning_models import HousingGroup
from core_apps.features.services.planning import require_planning
from core_apps.users.models import User
from core_apps.chat.models import Conversation, ConversationParticipant


def authorize(conversation, user, *, action="read_chat", lock=False):
    if conversation.kind == "company_request":
        from .company_access import authorize as company_authorize

        return company_authorize(conversation, user, action=action, lock=lock)
    # The same lock order is used by roster changes, sends and finalization.
    groups = HousingGroup.objects.select_for_update() if lock else HousingGroup.objects
    group = get_object_or_404(groups, pk=conversation.housing_group_id)
    fresh_user = User.objects.get(pk=user.pk)
    require_planning(fresh_user, "housing_groups")
    membership = group.memberships.filter(user=user, status="active").first()
    if (
        conversation.kind != "housing_group"
        or not membership
        or group.status != "active"
    ):
        raise PermissionDenied(
            "Group chat access is no longer available.", code="chat_access_revoked"
        )
    if lock:
        conversation = Conversation.objects.select_for_update().get(pk=conversation.pk)
    else:
        conversation = Conversation.objects.get(pk=conversation.pk)
    participant = ConversationParticipant.objects.filter(
        conversation=conversation,
        user=user,
        membership=membership,
        membership_revision=membership.joined_revision,
    ).first()
    if not participant or not participant.membership_period:
        raise PermissionDenied(
            "Group chat membership is unavailable.", code="chat_access_revoked"
        )
    if action not in actions(membership):
        raise PermissionDenied("This chat action is unavailable.")
    conversation.housing_group = group
    return conversation, participant, membership


def actions(membership):
    result = [
        "read_chat",
        "send_message",
        "upload_attachment",
        "mark_read",
        "set_notification_preference",
        "reply",
        "delete_own_message",
    ]
    if membership.role == "admin":
        result.append("delete_any_message")
    return result


def visible_messages(conversation, participant):
    return conversation.messages.filter(sequence__gte=participant.visible_from_sequence)


def unread_count(conversation, participant):
    return (
        visible_messages(conversation, participant)
        .filter(
            sequence__gt=participant.last_read_sequence,
            deleted_at__isnull=True,
        )
        .exclude(sender_id=participant.user_id)
        .exclude(kind="system")
        .count()
    )


def eligible_participants(conversation):
    if conversation.kind == "company_request":
        from .company_access import eligible_participants as company_participants

        return company_participants(conversation)
    from django.db.models import F

    return conversation.participant_set.filter(
        membership__status="active",
        membership__group_id=conversation.housing_group_id,
        membership_revision=F("membership__joined_revision"),
        user__is_active=True,
        user__is_verified=True,
    )


def total_unread_count(user):
    from django.db.models import Sum
    from rest_framework.exceptions import APIException

    total = (
        ConversationParticipant.objects.filter(
            user=user, conversation__kind="direct"
        ).aggregate(total=Sum("unread_count"))["total"]
        or 0
    )
    for conversation in Conversation.objects.filter(
        kind__in=["housing_group", "company_request"], participant_set__user=user
    ):
        try:
            _, participant, _ = authorize(conversation, user)
            total += unread_count(conversation, participant)
        except APIException:
            continue
    return total


def lock_conversation_root(conversation):
    if conversation.kind == "company_request":
        from .company_access import lock_root

        return lock_root(conversation)
    return HousingGroup.objects.select_for_update().get(
        pk=conversation.housing_group_id
    )
