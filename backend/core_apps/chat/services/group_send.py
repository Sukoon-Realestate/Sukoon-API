import hashlib
import json
from uuid import UUID
from django.db import transaction
from rest_framework.exceptions import ValidationError
from core_apps.chat.models import ChatAttachment, Message, ConversationParticipant
from django.db.models import F
from .group_access import authorize, visible_messages
from .group_limits import ChatConflict, limits
from .rich_media import validate_location


def normalize_request(data):
    permitted = {
        "client_message_id",
        "kind",
        "content",
        "attachment_ids",
        "reply_to_message_id",
        "membership_period",
        "location",
    }
    if not isinstance(data, dict) or set(data) - permitted:
        raise ValidationError("Unsupported message fields.")
    try:
        client_id = UUID(str(data["client_message_id"]))
        raw_ids = data.get("attachment_ids", [])
        if not isinstance(raw_ids, list):
            raise ValueError()
        attachment_ids = [str(UUID(str(value))) for value in raw_ids]
        reply_id = (
            str(UUID(str(data["reply_to_message_id"])))
            if data.get("reply_to_message_id")
            else None
        )
    except (KeyError, ValueError, TypeError):
        raise ValidationError("Supply valid message, reply and attachment identities.")
    content, kind = data.get("content", ""), data.get("kind", "text")
    if not isinstance(content, str):
        raise ValidationError({"content": "Supply text."})
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    policy = limits()
    if kind not in policy["message_kinds"]:
        raise ValidationError({"kind": "Unsupported message kind."})
    location = validate_location(data.get("location")) if kind == "location" else None
    if kind != "location" and data.get("location") is not None:
        raise ValidationError(
            {"location": "Only location messages may carry coordinates."}
        )
    if len(content) > policy["text_max_code_points"] or "\x00" in content:
        raise ValidationError(
            {
                "content": "Message text exceeds the limit or contains invalid characters."
            }
        )
    valid = (
        (kind == "text" and content.strip() and not attachment_ids)
        or (
            kind == "image" and 1 <= len(attachment_ids) <= policy["images_per_message"]
        )
        or (kind == "voice" and len(attachment_ids) == 1 and content == "")
        or (kind in {"file", "video"} and len(attachment_ids) == 1)
        or (kind == "location" and location is not None and not attachment_ids)
    )
    if not valid or len(set(attachment_ids)) != len(attachment_ids):
        raise ValidationError("Invalid message kind or attachment bundle.")
    canonical = {
        "kind": kind,
        "content": content,
        "attachment_ids": attachment_ids,
        "reply_to_message_id": reply_id,
    }
    if kind == "location":
        canonical["location"] = location
    fingerprint = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    return client_id, canonical, fingerprint


@transaction.atomic
def send_group_message(conversation, sender, data):
    from .group_events import record_event

    client_id, payload, fingerprint = normalize_request(data)
    conversation, participant, _ = authorize(
        conversation, sender, action="send_message", lock=True
    )
    if "membership_period" in data and str(data["membership_period"]) != str(
        participant.membership_period
    ):
        raise ChatConflict("Refresh the current chat membership before retrying.")
    existing = Message.objects.filter(
        conversation=conversation, sender=sender, client_message_id=client_id
    ).first()
    if existing:
        legacy_match = (
            conversation.kind == "direct"
            and not existing.payload_fingerprint
            and existing.kind == "text"
            and payload["kind"] == "text"
            and existing.content == payload["content"]
            and not payload["attachment_ids"]
            and not payload["reply_to_message_id"]
        )
        if existing.payload_fingerprint != fingerprint and not legacy_match:
            raise ChatConflict()
        if existing.sequence < participant.visible_from_sequence:
            raise ChatConflict(
                "This operation belongs to an earlier membership period."
            )
        return existing
    reply = None
    if payload["reply_to_message_id"]:
        reply = (
            visible_messages(conversation, participant)
            .filter(
                id=payload["reply_to_message_id"],
                deleted_at__isnull=True,
            )
            .exclude(kind="system")
            .first()
        )
        if not reply:
            raise ValidationError(
                {"reply_to_message_id": "This message is unavailable."}
            )
    attachments = []
    for identity in payload["attachment_ids"]:
        attachment = (
            ChatAttachment.objects.select_for_update()
            .filter(
                id=identity,
                conversation=conversation,
                uploader=sender,
                membership_period=participant.membership_period,
                state="ready",
                message__isnull=True,
                kind=payload["kind"],
            )
            .first()
        )
        if not attachment:
            raise ValidationError({"attachment_ids": "An attachment is unavailable."})
        attachments.append(attachment)
    conversation.last_sequence += 1
    message = Message.objects.create(
        conversation=conversation,
        sender=sender,
        client_message_id=client_id,
        kind=payload["kind"],
        content=payload["content"],
        reply_to=reply,
        sequence=conversation.last_sequence,
        payload_fingerprint=fingerprint,
        location=payload.get("location"),
    )
    for position, attachment in enumerate(attachments):
        attachment.message, attachment.state, attachment.position = (
            message,
            "attached",
            position,
        )
        attachment.save(update_fields=["message", "state", "position", "updated_at"])
    conversation.last_message_at = message.created_at
    # Group previews are always computed against the viewer's current boundary.
    conversation.last_message_preview = (
        (
            message.content
            or {
                "image": "📷",
                "voice": "🎙️",
                "file": "📎",
                "video": "🎬",
                "location": "📍",
            }.get(message.kind, "")
        )[:200]
        if conversation.kind == "direct"
        else ""
    )
    conversation.save(
        update_fields=[
            "last_sequence",
            "last_message_at",
            "last_message_preview",
            "updated_at",
        ]
    )
    if conversation.kind == "direct":
        ConversationParticipant.objects.filter(conversation=conversation).exclude(
            user=sender,
        ).update(unread_count=F("unread_count") + 1)
    record_event(conversation, "message.new", message=message, actor=sender)
    return message
