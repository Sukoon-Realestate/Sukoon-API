"""Message service: get or create direct conversation."""

import json
import logging
from typing import List
from asgiref.sync import async_to_sync
from django.core.cache import cache
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from core_apps.chat.models import Conversation, ConversationParticipant, Message


logger = logging.getLogger(__name__)


ONLINE_KEY_PREFIX = "chat:user:online:"


ONLINE_TTL_SECONDS = 300  # 5 minutes


class ChatMessageConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "client_message_id was already used for different content."
    default_code = "client_message_conflict"


def set_user_online_status(user_id: str, is_online: bool) -> None:
    """Cache online presence for a user in the cache layer."""
    try:
        key = f"{ONLINE_KEY_PREFIX}{user_id}"
        if is_online:
            cache.set(key, True, timeout=ONLINE_TTL_SECONDS)
        else:
            cache.delete(key)
    except Exception:
        logger.debug("Failed to set online status for user %s", user_id)


def is_user_online(user_id: str) -> bool:
    """Check whether a user has an active online presence."""
    try:
        return bool(cache.get(f"{ONLINE_KEY_PREFIX}{user_id}"))
    except Exception:
        return False


def direct_message_blocked(first_user, second_user, *, lock=False):
    from core_apps.features.planning_models import RoommateConnection
    from core_apps.chat.models import ChatBlock
    from django.db.models import Q
    if ChatBlock.objects.filter(Q(user=first_user, blocked_user=second_user) | Q(user=second_user, blocked_user=first_user)).exists():
        return True

    first, second = sorted([first_user.pk, second_user.pk])
    query = RoommateConnection.objects.filter(first_id=first, second_id=second)
    if lock:
        query = query.select_for_update()
    item = query.first()
    return item is not None and item.status != "accepted"


@transaction.atomic
def get_or_create_direct_conversation(*, user, other_user, workspace=None, rental_context=None) -> Conversation:
    """
    Return the canonical 1:1 conversation between two users, creating it if absent.

    Raises ValidationError if user tries to create a conversation with themselves.
    """
    if user.pk == other_user.pk:
        raise ValidationError(
            {"user_id": "You cannot start a conversation with yourself."}
        )

    from django.contrib.auth import get_user_model

    people = list(
        get_user_model()
        .objects.select_for_update()
        .filter(pk__in=[user.pk, other_user.pk])
        .order_by("pk")
    )
    if len(people) != 2 or not all(person.is_active for person in people):
        raise PermissionDenied("Both conversation participants must be active.")
    from core_apps.chat.services.conversation_preferences import contextual_conversation

    if workspace is None:
        # Calls without an explicit workspace are ordinary individual chats.
        # The app always supplies its current workspace; rental context still
        # identifies the owner when an internal caller only supplies a property.
        workspace = "individual"
        if isinstance(rental_context, dict) and rental_context.get("property_id"):
            from core_apps.properties.models import Property
            from django.core.exceptions import ValidationError as DjangoValidationError
            try:
                if Property.objects.filter(id=rental_context["property_id"], owner=user).exists():
                    workspace = "owner"
            except (ValueError, TypeError, DjangoValidationError):
                raise ValidationError({"rental_context": "Invalid property identity."})
    return contextual_conversation(user, other_user, workspace, rental_context)


def _notify_recipients(
    *, conversation: Conversation, sender, preview: str, message: Message
) -> None:
    """Push/in-app notify every participant except the sender of a new message."""
    recipients = (
        ConversationParticipant.objects.filter(conversation=conversation)
        .exclude(user=sender)
        .select_related("user")
    )
    from core_apps.chat.services.conversation_preferences import viewer_workspace
    for participant in recipients:
        if participant.is_muted:
            continue
        try:
            from core_apps.notifications.models import Notification
            from core_apps.notifications.services.notification_service import (
                NotificationService,
            )

            sender_name = sender.get_full_name or sender.email
            NotificationService.create_notification(
                user=participant.user,
                title=f"New message from {sender_name}",
                body=preview,
                notification_type=Notification.NotificationType.NEW_MESSAGE,
                category="chat",
                data={
                    "conversation_id": str(conversation.id),
                    "message_id": str(message.id),
                    "sender_id": str(sender.id),
                    "workspace": viewer_workspace(conversation, participant.user),
                },
                send_push=True,
            )
        except Exception:
            logger.exception(
                "Failed to notify recipient %s of new message %s",
                participant.user_id,
                message.id,
            )


def _broadcast_new_message(*, conversation: Conversation, message: Message) -> None:
    """Broadcast a new message event to all conversation participants."""
    try:
        from channels.layers import get_channel_layer
        from core_apps.chat.serializers.message import MessageSerializer

        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        # ? json round-trip coerces UUID/datetime to str so msgpack can serialize the payload
        payload = json.loads(
            json.dumps(dict(MessageSerializer(message).data), default=str)
        )
        participant_ids: List[str] = list(
            ConversationParticipant.objects.filter(
                conversation=conversation
            ).values_list("user__id", flat=True)
        )

        for uid in participant_ids:
            async_to_sync(channel_layer.group_send)(
                f"chat_user_{uid}",
                {"type": "chat.message", "payload": payload},
            )
    except Exception:
        logger.exception("Failed to broadcast new message %s", message.id)
