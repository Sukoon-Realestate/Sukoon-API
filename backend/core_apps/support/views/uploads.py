from datetime import timedelta
import uuid
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from core_apps.common.cookie_auth import CookieAuthentication
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.common.private_media_policy import inspect, maximum, policy
from core_apps.support.models import TicketAttachment, Ticket
from core_apps.support.services.staged_attachments import payload
from core_apps.support.services.payment_reports import can_read_ticket


class AttachmentPolicyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieAuthentication, SessionAuthentication]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request):
        from core_apps.features.services.evidence_storage import available

        enabled = available()
        return Response(
            {
                **policy(request.query_params.get("purpose") == "student"),
                "available": enabled,
                "blocking_reasons": (
                    [] if enabled else ["private_media_inspection_unavailable"]
                ),
                "max_attachments": (
                    3
                    if request.query_params.get("purpose", "support") == "support"
                    else 5
                ),
            },
            headers={"Cache-Control": "no-store"},
        )


class AttachmentUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieAuthentication, SessionAuthentication]
    renderer_classes = [GenericJsonRenderer]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            upload_id = uuid.UUID(str(request.data.get("client_upload_id")))
            creation = (
                uuid.UUID(str(request.data["creation_request_key"]))
                if request.data.get("creation_request_key")
                else None
            )
        except (ValueError, TypeError):
            raise ValidationError("Supply a valid upload identity.")
        workspace, ticket_id = request.data.get("workspace"), request.data.get(
            "ticket_id"
        )
        if workspace not in {"tenant", "owner", "student", "company", "account"} or bool(ticket_id) == bool(creation):
            raise ValidationError(
                "Supply exactly one ticket or creation request and a workspace."
            )
        ticket = None
        if ticket_id:
            try:
                ticket_id = uuid.UUID(str(ticket_id))
            except ValueError as error:
                raise ValidationError(
                    {"ticket_id": "Supply a valid ticket identity."}
                ) from error
            ticket = get_object_or_404(Ticket, id=ticket_id, workspace=workspace)
            if ticket.user_id != request.user.pk and not (
                request.user.is_staff and can_read_ticket(request.user, ticket)
            ):
                raise NotFound()
            if ticket.status in {"closed", "resolved"}:
                raise ValidationError("This ticket is closed.")
        file = request.FILES.get("file")
        if not file:
            raise ValidationError({"file": "Choose a file."})
        from core_apps.features.services.evidence_storage import require_available

        require_available()
        content = file.read(maximum(file.content_type) + 1)
        metadata = inspect(
            content, file.content_type, digest=request.data.get("sha256"), deep=False
        )
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            existing = TicketAttachment.objects.filter(
                uploader=request.user, client_upload_id=upload_id
            ).first()
            if existing:
                if (
                    existing.content_sha256 != metadata["sha256"]
                    or existing.pending_ticket_id != (ticket.pk if ticket else None)
                    or existing.creation_request_key != creation
                    or existing.workspace != workspace
                ):
                    raise ValidationError(
                        "The upload identity belongs to a different file or context."
                    )
                return Response(payload(existing))
            if (
                TicketAttachment.objects.filter(
                    uploader=request.user,
                    message__isnull=True,
                    expires_at__gt=timezone.now(),
                )
                .exclude(status__in=["expired", "unsafe", "failed"])
                .count()
                >= 12
            ):
                raise ValidationError(
                    "Finish or remove pending uploads before adding more."
                )
            item = TicketAttachment.objects.create(
                uploader=request.user,
                pending_ticket=ticket,
                creation_request_key=creation,
                client_upload_id=upload_id,
                workspace=workspace,
                name=file.name[:255],
                media_metadata=metadata,
                content_sha256=metadata["sha256"],
                private_content=content,
                status="pending",
                expires_at=timezone.now() + timedelta(hours=24),
            )
        return Response(payload(item), status=201)


class AttachmentUploadDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieAuthentication, SessionAuthentication]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request, id):
        item = get_object_or_404(
            TicketAttachment, uploader=request.user, client_upload_id=id
        )
        return Response(payload(item), headers={"Cache-Control": "no-store"})

    def delete(self, request, id):
        with transaction.atomic():
            item = get_object_or_404(
                TicketAttachment.objects.select_for_update(),
                uploader=request.user,
                client_upload_id=id,
                message__isnull=True,
            )
            item.status, item.expires_at, item.private_content = (
                "expired",
                timezone.now(),
                None,
            )
            item.save(update_fields=["status", "expires_at", "private_content"])
            # Cleanup waits for an active inspection lease and retries storage
            # outages; cancellation itself remains durable and idempotent.
        return Response(status=204)
