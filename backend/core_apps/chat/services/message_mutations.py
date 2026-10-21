"""Socket edits/deletions serialized with sends, membership changes and retries."""

import hashlib
import json
from uuid import UUID

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from core_apps.chat.models import ChatEvent
from .group_access import authorize, visible_messages
from .group_events import record_event
from .group_limits import ChatConflict, limits
from .group_operations import delete_group_message
from .group_projection import message_payload


@transaction.atomic
def mutate_message(conversation, user, data):
    kind = data.get("type")
    if kind not in {"message.edit", "message.delete"}:
        raise ValidationError("Unsupported message operation.")
    permitted = {
        "type",
        "protocol",
        "conversation_id",
        "operation_id",
        "message_id",
        "expected_revision",
        "membership_period",
    } | ({"content"} if kind == "message.edit" else set())
    if set(data) - permitted:
        raise ValidationError("Unsupported operation fields.")
    try:
        operation_id = str(UUID(str(data["operation_id"])))
        identity = UUID(str(data["message_id"]))
    except (KeyError, ValueError, TypeError):
        raise ValidationError("Supply valid message and operation identities.")
    expected = data.get("expected_revision")
    if type(expected) is not int or expected < 1:
        raise ValidationError("Supply the reviewed message revision.")
    conversation, participant, member = authorize(conversation, user, lock=True)
    if str(data.get("membership_period")) != str(participant.membership_period):
        raise ChatConflict("Refresh the current chat membership before retrying.")
    message = visible_messages(conversation, participant).filter(id=identity).first()
    if not message:
        raise NotFound()
    if message.kind == "system" or (
        message.sender_id != user.pk
        and (kind == "message.edit" or member.role != "admin")
    ):
        raise PermissionDenied()
    content = data.get("content", "")
    if not isinstance(content, str):
        raise ValidationError({"content": "Supply text."})
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    fingerprint = hashlib.sha256(
        json.dumps(
            [
                kind,
                str(identity),
                expected,
                content,
                str(participant.membership_period),
            ],
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    receipt = ChatEvent.objects.filter(
        conversation=conversation,
        actor=user,
        data__operation_id=operation_id,
    ).first()
    if receipt:
        if receipt.data.get("fingerprint") != fingerprint:
            raise ChatConflict()
        return message_payload(message, participant, member)
    if message.revision != expected or message.deleted_at:
        raise ChatConflict("This message changed. Reload it before continuing.")
    event_data = {"operation_id": operation_id, "fingerprint": fingerprint}
    if kind == "message.delete":
        return delete_group_message(conversation, user, identity, event_data=event_data)
    # Reading history after consent withdrawal does not grant editing authority.
    authorize(conversation, user, action="send_message", lock=True)
    if message.kind not in {"text", "image"}:
        raise ValidationError("Only text and image captions can be edited.")
    if (message.kind == "text" and not content.strip()) or (
        len(content) > limits()["text_max_code_points"] or "\x00" in content
    ):
        raise ValidationError(
            {"content": "Supply valid message text within the limit."}
        )
    message.content = content
    message.edited_at = timezone.now()
    message.revision += 1
    message.save(update_fields=["content", "edited_at", "revision", "updated_at"])
    # Keep the original send fingerprint immutable: a delayed original send must
    # return this same message, never restore the previous text or create a copy.
    if conversation.kind == "direct" and message.sequence == conversation.last_sequence:
        conversation.last_message_preview = (content or "📷")[:200]
        conversation.save(update_fields=["last_message_preview"])
    record_event(
        conversation, "message.edited", message=message, actor=user, data=event_data
    )
    record_event(conversation, "conversation.updated", actor=user)
    return message_payload(message, participant, member)
