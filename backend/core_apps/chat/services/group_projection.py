"""Per-viewer projections: hidden history and tombstones never expose media."""

from .group_access import (
    actions,
    authorize,
    eligible_participants,
    unread_count,
    visible_messages,
)
from .group_limits import limits


def sender_payload(user):
    from core_apps.features.services.planning import display_name
    from core_apps.chat.serializers.participant import ParticipantSerializer

    return {
        "id": str(user.id),
        "name": display_name(user),
        "avatar_url": ParticipantSerializer().get_avatar_url(user) or None,
    }


def attachment_payload(attachment):
    base = (
        f"chat/conversations/{attachment.conversation.id}/attachments/{attachment.id}"
    )
    return {
        "id": str(attachment.id),
        "client_upload_id": str(attachment.client_upload_id),
        "kind": attachment.kind,
        "state": attachment.state,
        "mime_type": attachment.mime_type,
        "size_bytes": attachment.byte_size,
        "width": attachment.width,
        "height": attachment.height,
        "duration_ms": attachment.duration_ms,
        "content_path": f"{base}/content/",
        "thumbnail_path": f"{base}/thumbnail/" if attachment.thumbnail_key else None,
    }


def message_payload(message, participant, membership):
    deleted = message.deleted_at is not None
    readers = (
        eligible_participants(message.conversation)
        .filter(
            visible_from_sequence__lte=message.sequence,
        )
        .exclude(user_id=message.sender_id)
    )
    permitted = (
        []
        if deleted or message.kind == "system" or "reply" not in actions(membership)
        else ["reply"]
    )
    if (
        not deleted
        and message.kind != "system"
        and (message.sender_id == participant.user_id or membership.role == "admin")
    ):
        permitted.append("delete_message")
    reply = None
    if message.reply_to_id and not deleted:
        original = message.reply_to
        if original.sequence < participant.visible_from_sequence or original.deleted_at:
            reply = {"id": str(original.id), "availability": "unavailable"}
        else:
            reply = {
                "id": str(original.id),
                "availability": "available",
                "kind": original.kind,
                "sender_name": sender_payload(original.sender)["name"],
                "content_preview": original.content[:160],
            }
    return {
        "id": str(message.id),
        "conversation_id": str(message.conversation.id),
        "client_message_id": (
            str(message.client_message_id) if message.client_message_id else None
        ),
        "sequence": message.sequence,
        "kind": message.kind,
        "status": "sent",
        "content": "" if deleted else message.content,
        "sender": sender_payload(message.sender),
        "created_at": message.created_at.isoformat(),
        "is_deleted": deleted,
        "reply_to": reply,
        "attachments": (
            []
            if deleted
            else [attachment_payload(a) for a in message.attachments.all()]
        ),
        "system": (
            message.system_data if message.kind == "system" and not deleted else None
        ),
        "read_by_count": readers.filter(
            last_read_sequence__gte=message.sequence
        ).count(),
        "eligible_reader_count": readers.count(),
        "allowed_actions": permitted,
    }


def summary(conversation, user):
    from .group_cursors import encode_cursor

    conversation, participant, member = authorize(conversation, user)
    latest = visible_messages(conversation, participant).order_by("-sequence").first()
    preview = None
    if latest:
        preview = {
            "kind": latest.kind,
            "is_deleted": bool(latest.deleted_at),
            "content": latest.content[:160] if not latest.deleted_at else "",
        }
    company = conversation.kind == "company_request"
    direct = conversation.kind == "direct"
    request = conversation.company_request if company else None
    other = conversation.participants.exclude(pk=user.pk).first() if direct else None
    return {
        "id": str(conversation.id),
        "conversation_id": str(conversation.id),
        "conversation_type": conversation.kind,
        "group_id": None if company or direct else str(conversation.housing_group.id),
        **(
            {
                "company_id": str(request.company.id),
                "company_name": request.company.name,
                "request_id": str(request.id),
            }
            if company
            else {}
        ),
        "title": (
            (sender_payload(other)["name"] if other else "")
            if direct
            else request.title if company else conversation.housing_group.name
        ),
        "active_member_count": eligible_participants(conversation).count(),
        "membership_id": str(member.id),
        "membership_period": str(participant.membership_period),
        "visible_from_sequence": participant.visible_from_sequence,
        "last_read_sequence": participant.last_read_sequence,
        "last_sequence": conversation.last_sequence,
        "unread_count": unread_count(conversation, participant),
        "is_muted": participant.is_muted,
        "allowed_actions": actions(member),
        "limits": limits(),
        "can_send": "send_message" in actions(member),
        # Exact sender/client identity and payload are serialized by group_send.
        # A retry may additionally fence its original membership period.
        "idempotent_message_retry": True,
        "last_message": preview,
        "last_message_at": latest.created_at.isoformat() if latest else None,
        "event_cursor": encode_cursor(
            conversation, participant, "events", conversation.last_event_sequence
        ),
    }


def card_projection(group, user):
    from rest_framework.exceptions import APIException
    from core_apps.chat.models import Conversation

    conversation = Conversation.objects.filter(housing_group=group).first()
    if not conversation:
        return {"available": False, "unread_count": 0}
    try:
        _, participant, _ = authorize(conversation, user)
    except APIException:
        return {"available": False, "unread_count": 0}
    return {
        "available": True,
        "conversation_id": str(conversation.id),
        "unread_count": unread_count(conversation, participant),
    }
