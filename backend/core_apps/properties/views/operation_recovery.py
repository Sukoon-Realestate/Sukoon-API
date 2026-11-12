"""Return original authoritative acknowledgment or fence an uncommitted command."""

from ..services.operation_recovery import resolve_listing_operation
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import UUIDField
from core_apps.common.idempotency import request_key
from core_apps.common.renderers import GenericJsonRenderer


class PropertyOperationRecovery(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request):
        if request.data.get("kind") == "image.upload":
            from ..services.image_uploads import reconcile

            identity = UUIDField().run_validation(request.data.get("property_id"))
            reconcile(
                user=request.user,
                claims=request.auth,
                property_id=identity,
                key=request_key(request),
            )
        return Response(
            resolve_listing_operation(
                request.user,
                request.data,
                auth=request.auth,
                idempotency_key=request_key(request),
            ),
            headers={"Cache-Control": "no-store"},
        )
