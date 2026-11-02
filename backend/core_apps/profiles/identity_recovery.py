from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core_apps.common.idempotency import resolve_or_close
from core_apps.common.renderers import GenericJsonRenderer


class IdentityOperationResolveAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request, operation_id):
        record = resolve_or_close(
            user=request.user, operation="identity.submit", key=str(operation_id),
            auth_claims=request.auth,
        )
        return Response({
            "operation_id": str(operation_id),
            "status": record.recovery_status,
            "result": record.response_data if record.recovery_status == "confirmed" else None,
        }, headers={"Cache-Control": "private, no-store"})
