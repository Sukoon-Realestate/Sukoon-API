from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.common.idempotency import request_key, resolve_or_close
from core_apps.features.models import IdempotencyRecord
from core_apps.support.models import Ticket
from core_apps.support.services import get_ticket_detail
from core_apps.support.serializers import TicketDetailSerializer


class TicketReplyReceiptAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request, id):
        return self.project(request, id, False)

    def post(self, request, id):
        return self.project(request, id, True)

    def project(self, request, id, close):
        try:
            ticket = get_ticket_detail(
                request.user, id, workspace=request.query_params.get("workspace")
            )
        except Ticket.DoesNotExist:
            raise NotFound()
        key = request_key(request)
        if not key:
            raise ValidationError("Supply the original Idempotency-Key.")
        operation = f"support.ticket.reply:{ticket.id}"
        record = (
            resolve_or_close(
                user=request.user,
                operation=operation,
                key=key,
                auth_claims=request.auth,
            )
            if close
            else IdempotencyRecord.objects.filter(
                user=request.user, operation=operation, request_key=key
            ).first()
        )
        outcome = "unknown"
        if record and record.recovery_status == "absent_final":
            outcome = "absent_final"
        if (
            record
            and record.recovery_status == "confirmed"
            and ticket.messages.filter(id=record.result_subject_id).exists()
        ):
            outcome = "acknowledged"
        return Response(
            {
                "outcome": outcome,
                "request_key": key,
                "ticket": (
                    TicketDetailSerializer(
                        get_ticket_detail(request.user, id),
                        context={"request": request},
                    ).data
                    if outcome == "acknowledged"
                    else None
                ),
            },
            headers={"Cache-Control": "no-store"},
        )
