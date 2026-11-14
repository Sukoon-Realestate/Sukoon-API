"""Message service: send message."""

from asgiref.sync import async_to_sync
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.chat.models import Conversation, ConversationParticipant
from .get_or_create_direct_conversation import (
    logger,
    ChatMessageConflict,
)


def send_message(*, conversation, sender, content, client_message_id=None):
    from ..commands import SendCommand, send
    from ..group_limits import ChatConflict

    if conversation.kind == "direct" and not ConversationParticipant.objects.filter(
        conversation=conversation, user=sender
    ).exists():
        raise ValidationError({"content": "You are not a participant in this conversation."})
    try:
        return send(conversation, sender, SendCommand.legacy_text(content, client_message_id))
    except ChatConflict as exc:
        # The original protocol keeps its established conflict code and text.
        raise ChatMessageConflict() from exc


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
    if conversation.kind in {"housing_group", "company_request"}:
        raise ValidationError("Group reads require an explicit last_read_sequence.")
    if not ConversationParticipant.objects.filter(
        conversation=conversation, user=user
    ).exists():
        raise PermissionDenied("Not a participant.")
    from ..direct_access import lock_root, prepare_locked
    from ..group_operations import mark_group_read

    conversation = prepare_locked(lock_root(conversation))
    mark_group_read(conversation, user, conversation.last_sequence)
    # Preserve the legacy read acknowledgement and empty-conversation timestamp.
    ConversationParticipant.objects.filter(conversation=conversation, user=user).update(
        last_read_at=timezone.now(),
        unread_count=0,
    )
    if conversation.last_sequence == 0:
        transaction.on_commit(
            lambda: _broadcast_read_receipt(conversation=conversation, reader=user)
        )
