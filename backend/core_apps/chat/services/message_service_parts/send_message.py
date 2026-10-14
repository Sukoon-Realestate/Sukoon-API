"""Message service: send message."""

from asgiref.sync import async_to_sync
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.chat.models import Conversation, ConversationParticipant, Message
from .get_or_create_direct_conversation import (
    logger,
    ChatMessageConflict,
    direct_message_blocked,
    _notify_recipients,
    _broadcast_new_message,
)


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


@transaction.atomic
def mark_conversation_read(*, conversation: Conversation, user) -> None:
    """
    Mark all messages in a conversation as read for a user.
    Resets unread_count and sets last_read_at. Broadcasts a read receipt.
    """
    updated = ConversationParticipant.objects.filter(
        conversation=conversation,
        user=user,
    ).update(last_read_at=timezone.now(), unread_count=0)
    if not updated:
        raise PermissionDenied("Not a participant.")

    transaction.on_commit(
        lambda: _broadcast_read_receipt(conversation=conversation, reader=user)
    )
