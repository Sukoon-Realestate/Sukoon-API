"""Per-viewer projections: hidden history and tombstones never expose media."""

from datetime import timedelta
from django.utils import timezone

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
        "original_name": attachment.original_name,
        "waveform": attachment.waveform,
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
        if timezone.now() <= message.created_at + timedelta(hours=1):
            permitted.append("delete_message")
    if (
        not deleted
        and message.kind in {"text", "image"}
        and message.sender_id == participant.user_id
        and "send_message" in actions(membership)
    ):
        permitted.append("edit_message")
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
                "attachment_name": next((a.original_name for a in original.attachments.all()), ""),
                "attachments": [attachment_payload(a) for a in original.attachments.all()],

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
        "location": None if deleted else message.location,
        "sender": sender_payload(message.sender),
        "created_at": message.created_at.isoformat(),
        "is_deleted": deleted,
        "revision": message.revision,
        "edited_at": (
            message.edited_at.isoformat() if message.edited_at and not deleted else None
        ),
        "edit_history": [] if deleted else [
            {"revision": edit.revision, "before": edit.before, "after": edit.after, "edited_at": edit.created_at.isoformat()}
            for edit in message.edits.all()
        ],
        "delete_before": (message.created_at + timedelta(hours=1)).isoformat(),
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
    from core_apps.chat.moderation.policy import projection as policy_projection
    from .group_cursors import encode_cursor

    from .conversation_preferences import preferences_payload
    conversation, participant, member = authorize(conversation, user)
    latest = visible_messages(conversation, participant).order_by("-sequence").first()
    preview = conversation_preview(latest, user)
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
        **preferences_payload(conversation, user, participant),
        "allowed_actions": actions(member),
        "limits": limits(),
        "can_send": "send_message" in actions(member),
        "policy": policy_projection(conversation, user),
        # Exact sender/client identity and payload are serialized by group_send.
        # A retry may additionally fence its original membership period.
        "idempotent_message_retry": True,
        "last_message": preview,
        "last_message_at": latest.created_at.isoformat() if latest else None,
        "event_cursor": encode_cursor(
            conversation, participant, "events", conversation.last_event_sequence
        ),
    }


def conversation_preview(message, viewer):
    """Minimal inbox preview; receipts use the same eligible roster as history.

    Incoming unread counts remain independent of the recipient's read receipt
    for an outgoing message. No message bodies/media survive a tombstone.
    """
    if message is None:
        return None
    read_count = eligible_count = None
    if (
        message.sender_id == viewer.pk
        and not message.deleted_at
        and message.kind != "system"
    ):
        readers = eligible_participants(message.conversation).exclude(user_id=viewer.pk)
        if message.sequence is not None:
            readers = readers.filter(visible_from_sequence__lte=message.sequence)
            read_count = readers.filter(
                last_read_sequence__gte=message.sequence
            ).count()
        else:
            # Legacy direct messages have not yet acquired sequence numbers.
            read_count = readers.filter(last_read_at__gte=message.created_at).count()
        eligible_count = readers.count()
    return {
        "id": str(message.id),
        "sequence": message.sequence,
        "sender_id": str(message.sender_id),
        "kind": message.kind,
        "is_deleted": bool(message.deleted_at),
        "content": message.content[:160] if not message.deleted_at else "",
        "read_by_count": read_count,
        "eligible_reader_count": eligible_count,
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
