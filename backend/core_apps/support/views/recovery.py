"""Read an original creation receipt without replaying a business command."""

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.idempotency import request_key
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.features.models import IdempotencyRecord
from core_apps.support.models import Ticket
from core_apps.support.serializers import TicketDetailSerializer
from core_apps.support.services import get_ticket_detail


class TicketCreationReceiptAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request):
        workspace = request.query_params.get("workspace")
        key = request_key(request)
        if workspace not in {"tenant", "owner"} or not key:
            raise ValidationError(
                "Supply a workspace and the original Idempotency-Key."
            )
        record = IdempotencyRecord.objects.filter(
            user=request.user,
            operation=f"support.ticket.create:{workspace}",
            request_key=key,
        ).first()
        # Missing is deliberately unknown: a concurrent transaction may still
        # commit. Neither an absent row nor a similar ticket permits resending.
        data = {"outcome": "unknown", "request_key": key, "ticket": None}
        if (
            record
            and record.recovery_status == "confirmed"
            and record.result_subject_id
        ):
            try:
                ticket = get_ticket_detail(
                    request.user, str(record.result_subject_id), workspace=workspace
                )
            except Ticket.DoesNotExist:
                pass
            else:
                data.update(
                    outcome="acknowledged",
                    ticket=TicketDetailSerializer(
                        ticket, context={"request": request}
                    ).data,
                )
        return Response(data, headers={"Cache-Control": "no-store"})
