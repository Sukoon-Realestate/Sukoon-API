import json
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.utils.http import content_disposition_header
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core_apps.chat.models import ChatAttachment, Conversation
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.group_limits import limits
from core_apps.chat.services.group_media_storage import (
    read_private_path,
    upload_attachment,
)
from core_apps.chat.services.group_projection import attachment_payload
from core_apps.chat.services.group_rate_limit import enforce_rate


class BoundedChatUploadHandler(TemporaryFileUploadHandler):
    def __init__(self, request):
        super().__init__(request)
        self.total = 0
        self.files = 0

    def new_file(self, *args, **kwargs):
        self.files += 1
        if self.files > 1:
            raise ValidationError({"file": "Upload one attachment per request."})
        return super().new_file(*args, **kwargs)

    def receive_data_chunk(self, raw_data, start):
        self.total += len(raw_data)
        if self.total > max(
            limits()[f"{kind}_max_bytes"]
            for kind in ("image", "voice", "file", "video")
        ):
            self.file.close()
            raise ValidationError({"file": "Attachment exceeds the byte limit."})
        return super().receive_data_chunk(raw_data, start)


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


class GroupAttachmentUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def initialize_request(self, request, *args, **kwargs):
        request.upload_handlers = [BoundedChatUploadHandler(request)]
        return super().initialize_request(request, *args, **kwargs)

    def post(self, request, id):
        enforce_rate(request.user, "upload", maximum=20)
        conversation = get_object_or_404(Conversation, id=id)
        authorize(conversation, request.user, action="upload_attachment")
        if set(request.data) - {
            "file",
            "client_upload_id",
            "kind",
            "sha256",
            "waveform",
        }:
            raise ValidationError("Unsupported attachment fields.")
        upload = request.FILES.get("file")
        if not upload:
            raise ValidationError({"file": "Supply an attachment."})
        try:
            waveform = (
                json.loads(request.data["waveform"])
                if "waveform" in request.data
                else None
            )
        except (ValueError, TypeError):
            raise ValidationError({"waveform": "Supply a numeric waveform."})
        item = upload_attachment(
            conversation,
            request.user,
            upload,
            request.data.get("client_upload_id"),
            request.data.get("kind"),
            request.data.get("sha256"),
            waveform=waveform,
        )
        return Response(attachment_payload(item), status=201)


class GroupAttachmentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def get(self, request, id, attachment_id=None, client_id=None, content=None):
        conversation, _, _ = authorize(
            get_object_or_404(Conversation, id=id), request.user, lock=True
        )
        item = accessible_attachment(
            conversation, request.user, identity=attachment_id, client_id=client_id
        )
        if not content:
            return Response(attachment_payload(item))
        if content not in {"content", "thumbnail"}:
            raise NotFound()
        key = item.thumbnail_key if content == "thumbnail" else item.storage_key
        if not key:
            raise NotFound()
        try:
            source = read_private_path(key).open("rb")
        except FileNotFoundError:
            raise NotFound("Attachment is unavailable.")
        response = FileResponse(
            source,
            content_type="image/jpeg" if content == "thumbnail" else item.mime_type,
        )
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Disposition"] = content_disposition_header(
            item.kind == "file" and content == "content",
            item.original_name or "attachment",
        )
        return response
