"""Owner-only weekly preview and explicit additive commit."""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from ..services.weekly_availability import set_weekly_availability


class OwnerAvailabilityAPIView(APIView):
    http_method_names = ["post", "put", "options"]
    name = "Owner Availability"
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request, property_id):
        return Response(
            set_weekly_availability(
                request.user, property_id, request.data, auth=request.auth
            )
        )

    def put(self, request, property_id):
        return Response(
            set_weekly_availability(
                request.user, property_id, request.data, commit=True, auth=request.auth
            )
        )
