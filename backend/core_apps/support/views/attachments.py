import io
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
    renderer_classes = [GenericJsonRenderer]

    def get(self, request, id):

        if not request.user.is_active:
            raise PermissionDenied()
        attachment = get_object_or_404(
            TicketAttachment.objects.select_related("message__ticket"), id=id
        )
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
                content = clean_image(stream)
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
        response = FileResponse(io.BytesIO(content), content_type="image/jpeg")
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Disposition"] = 'inline; filename="support-attachment.jpg"'
        return response
