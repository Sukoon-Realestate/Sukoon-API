import json
import logging
from typing import List

from asgiref.sync import async_to_sync
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone
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

    first, second = sorted([first_user.pk, second_user.pk])
    query = RoommateConnection.objects.filter(first_id=first, second_id=second)
    if lock:
        query = query.select_for_update()
    item = query.first()
    return item is not None and item.status != "accepted"


@transaction.atomic
def get_or_create_direct_conversation(*, user, other_user) -> Conversation:
    """
    Return the canonical 1:1 conversation between two users, creating it if absent.

    Raises ValidationError if user tries to create a conversation with themselves.
    """
    if user.pk == other_user.pk:
        raise ValidationError(
            {"user_id": "You cannot start a conversation with yourself."}
        )

    if direct_message_blocked(user, other_user, lock=True):
        raise PermissionDenied("Messaging consent is not active for this connection.")

    # Find an existing conversation shared by both users
    existing = (
        Conversation.objects.filter(participant_set__user=user)
        .filter(participant_set__user=other_user)
        .distinct()
        .first()
    )
    if existing:
        return existing

    conversation = Conversation.objects.create()
    ConversationParticipant.objects.bulk_create(
        [
            ConversationParticipant(conversation=conversation, user=user),
            ConversationParticipant(conversation=conversation, user=other_user),
        ]
    )
    return conversation


@transaction.atomic
def send_message(
    *, conversation: Conversation, sender, content: str, client_message_id=None
) -> Message:
    """
    Create a message, update conversation preview, increment recipients' unread counts,
    and broadcast to all participants via the channel layer.
    """
    # Guard: sender must be a participant in the conversation
    if not ConversationParticipant.objects.filter(
        conversation=conversation, user=sender
    ).exists():
        raise ValidationError(
            {"content": "You are not a participant in this conversation."}
        )

    for recipient in conversation.participants.exclude(pk=sender.pk):
        if direct_message_blocked(sender, recipient, lock=True):
            raise PermissionDenied(
                "Messaging consent is not active for this connection."
            )

    if client_message_id:
        existing = Message.objects.filter(
            conversation=conversation,
            sender=sender,
            client_message_id=client_message_id,
        ).first()
        if existing:
            if existing.content != content:
                raise ChatMessageConflict()
            return existing
    try:
        # The savepoint keeps the surrounding transaction usable when REST and
        # WebSocket race on the same database uniqueness constraint.
        with transaction.atomic():
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=content,
                client_message_id=client_message_id,
            )
    except IntegrityError:
        if not client_message_id:
            raise
        message = Message.objects.get(
            conversation=conversation,
            sender=sender,
            client_message_id=client_message_id,
        )
        if message.content != content:
            raise ChatMessageConflict()
        return message

    preview = content[:200] if len(content) > 200 else content
    Conversation.objects.filter(pk=conversation.pk).update(
        last_message_at=message.created_at,
        last_message_preview=preview,
    )

    # Increment unread count for every participant except the sender
    ConversationParticipant.objects.filter(
        conversation=conversation,
    ).exclude(
        user=sender
    ).update(unread_count=F("unread_count") + 1)

    # Broadcast via channel layer and notify recipients on transaction commit
    transaction.on_commit(
        lambda: _broadcast_new_message(conversation=conversation, message=message)
    )
    transaction.on_commit(
        lambda: _notify_recipients(
            conversation=conversation, sender=sender, preview=preview, message=message
        )
    )

    return message


def _notify_recipients(
    *, conversation: Conversation, sender, preview: str, message: Message
) -> None:
    """Push/in-app notify every participant except the sender of a new message."""
    recipients = (
        ConversationParticipant.objects.filter(conversation=conversation)
        .exclude(user=sender)
        .select_related("user")
    )
    for participant in recipients:
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


@transaction.atomic
def mark_conversation_read(*, conversation: Conversation, user) -> None:
    """
    Mark all messages in a conversation as read for a user.
    Resets unread_count and sets last_read_at. Broadcasts a read receipt.
    """
    ConversationParticipant.objects.filter(
        conversation=conversation,
        user=user,
    ).update(last_read_at=timezone.now(), unread_count=0)

    transaction.on_commit(
        lambda: _broadcast_read_receipt(conversation=conversation, reader=user)
    )


def _broadcast_read_receipt(*, conversation: Conversation, reader) -> None:
    """Broadcast a read receipt to the other participants."""
    try:
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        other_ids = list(
            ConversationParticipant.objects.filter(conversation=conversation)
            .exclude(user=reader)
            .values_list("user__id", flat=True)
        )
        payload = {
            "conversation_id": str(conversation.id),
            "reader_id": str(reader.id),
        }
        for uid in other_ids:
            async_to_sync(channel_layer.group_send)(
                f"chat_user_{uid}",
                {"type": "chat.read", "payload": payload},
            )
    except Exception:
        logger.exception(
            "Failed to broadcast read receipt for conversation %s", conversation.id
        )
