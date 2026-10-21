from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from .group_access import authorize, unread_count, visible_messages
from .group_events import record_event
from .group_projection import message_payload, summary


@transaction.atomic
def mark_group_read(conversation, user, sequence):
    conversation, participant, _ = authorize(
        conversation, user, action="mark_read", lock=True
    )
    if (
        type(sequence) is not int
        or sequence < 0
        or (
            sequence > 0
            and not visible_messages(conversation, participant)
            .filter(sequence=sequence)
            .exists()
        )
    ):
        raise ValidationError(
            {"last_read_sequence": "Supply a visible, persisted message sequence."}
        )
    if sequence > participant.last_read_sequence:
        participant.last_read_sequence, participant.last_read_at = (
            sequence,
            timezone.now(),
        )
        participant.save(
            update_fields=["last_read_sequence", "last_read_at", "updated_at"]
        )
        if conversation.kind == "direct":
            participant.unread_count = unread_count(conversation, participant)
            participant.save(update_fields=["unread_count"])
        record_event(
            conversation,
            "message.read",
            actor=user,
            data={"membership_period": str(participant.membership_period)},
        )
    return {
        "conversation_id": str(conversation.id),
        "last_read_sequence": participant.last_read_sequence,
        "unread_count": unread_count(conversation, participant),
    }


@transaction.atomic
def delete_group_message(conversation, user, identity, *, event_data=None):
    conversation, participant, member = authorize(conversation, user, lock=True)
    message = visible_messages(conversation, participant).filter(id=identity).first()
    if not message:
        raise NotFound()
    if message.kind == "system" or (
        message.sender_id != user.pk and member.role != "admin"
    ):
        raise PermissionDenied()
    if not message.deleted_at:
        message.revision += 1
        message.deleted_at, message.deleted_by = timezone.now(), user
        message.content, message.reply_to = "", None
        message.save(
            update_fields=[
                "deleted_at",
                "deleted_by",
                "content",
                "reply_to",
                "updated_at",
                "revision",
            ]
        )
        message.attachments.update(state="revoked")
        if conversation.kind == "direct":
            # The legacy inbox remains in use by conversation lists/old clients.
            # A deleted message must not survive in its preview or unread count.
            if message.sequence == conversation.last_sequence:
                conversation.last_message_preview = ""
                conversation.save(update_fields=["last_message_preview"])
            for recipient in conversation.participant_set.all():
                recipient.unread_count = unread_count(conversation, recipient)
                recipient.save(update_fields=["unread_count"])
        # Authorization is revoked in this transaction. Physical derivatives are
        # removed by the periodic cleanup worker, which can safely retry I/O.
        record_event(
            conversation,
            "message.deleted",
            message=message,
            actor=user,
            data=event_data,
        )
        record_event(conversation, "conversation.updated", actor=user)
    return message_payload(message, participant, member)


@transaction.atomic
def set_preference(conversation, user, muted):
    conversation, participant, _ = authorize(
        conversation, user, action="set_notification_preference", lock=True
    )
    if type(muted) is not bool:
        raise ValidationError({"is_muted": "Supply a boolean."})
    if participant.is_muted != muted:
        participant.is_muted = muted
        participant.save(update_fields=["is_muted", "updated_at"])
        record_event(conversation, "conversation.updated", actor=user)
    return summary(conversation, user)
