import io
import hashlib
from rest_framework.authentication import SessionAuthentication
from core_apps.common.cookie_auth import CookieAuthentication
from core_apps.common.private_media_policy import maximum, MIME_EXTENSIONS
from core_apps.common.private_storage import PrivateStorageUnavailable
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, PermissionDenied
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.support.models import TicketAttachment
from core_apps.support.services.payment_reports import can_read_ticket
from core_apps.support.services.private_attachments import clean_image


class TicketAttachmentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieAuthentication, SessionAuthentication]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request, id):

        if not request.user.is_active:
            raise PermissionDenied()
        attachment = get_object_or_404(
            TicketAttachment.objects.select_related("message__ticket").filter(
                message__isnull=False
            ),
            id=id,
        )
        if attachment.status not in {None, "attached"}:
            raise NotFound()
        ticket = attachment.message.ticket
        owner = (
            ticket.user_id == request.user.pk
            and request.query_params.get("workspace") == ticket.workspace
        )
        # Operator access uses current console-role authority and is audited.
        # An attachment identifier never grants a consumer another user's media.
        operator = request.user.is_staff and can_read_ticket(request.user, ticket)
        if not owner and not operator:
            raise NotFound()
        field = attachment.private_file or attachment.file
        if not field:
            raise NotFound()
        try:
            with field.open("rb") as stream:
                mime = (attachment.media_metadata or {}).get("mime_type", "image/jpeg")
                original = stream.read(maximum(mime) + 1)
                if len(original) > maximum(mime) or (
                    attachment.content_sha256
                    and hashlib.sha256(original).hexdigest()
                    != attachment.content_sha256
                ):
                    raise PrivateStorageUnavailable(
                        "Private attachment integrity check failed."
                    )
                if attachment.status == "attached":
                    metadata = attachment.media_metadata or {}
                    if (
                        mime not in MIME_EXTENSIONS
                        or metadata.get("sha256") != attachment.content_sha256
                        or metadata.get("size_bytes") != len(original)
                    ):
                        raise PrivateStorageUnavailable(
                            "Private attachment inspection metadata is unavailable."
                        )
                    content = original
                else:
                    content = clean_image(io.BytesIO(original))
                    mime = "image/jpeg"
        except OSError as error:
            raise NotFound() from error
        if operator and not owner:
            from core_apps.features.models import RentalAuditEvent

            RentalAuditEvent.objects.create(
                actor=request.user,
                subject_kind="support_attachment",
                subject_id=attachment.id,
                subject_revision=ticket.revision,
                action="support.attachment_read",
                reason="Support ticket evidence review",
            )
        response = FileResponse(io.BytesIO(content), content_type=mime)
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        disposition = "inline" if mime.startswith("image/") else "attachment"
        response["Content-Disposition"] = (
            f'{disposition}; filename="support-attachment.{MIME_EXTENSIONS[mime]}"'
        )
        return response
