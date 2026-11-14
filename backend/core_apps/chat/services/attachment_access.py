"""Fresh attachment authority, shared by bytes, discovery and transcription."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from core_apps.chat.models import ChatAttachment
from .group_access import authorize


def accessible_attachment(conversation, user, *, identity=None, client_id=None):
    conversation, participant, _ = authorize(conversation, user)
    query = ChatAttachment.objects.filter(conversation=conversation).select_related(
        "message", "conversation"
    )
    item = get_object_or_404(
        query,
        **(
            {"id": identity}
            if identity
            else {"uploader": user, "client_upload_id": client_id}
        ),
    )
    if item.message_id:
        if (
            item.message.sequence < participant.visible_from_sequence
            or item.message.deleted_at
            or item.state != "attached"
        ):
            raise NotFound()
    elif (
        item.uploader_id != user.pk
        or item.membership_period != participant.membership_period
        or item.state != "ready"
    ):
        raise NotFound()
    return item
