from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from ..services.saved_search_reads import acknowledge


class AcknowledgeSavedSearchAPIView(APIView):
    http_method_names = ["post", "options"]
    name = "Acknowledge Saved Search"
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request, read_id):
        return Response(
            acknowledge(request.user, read_id, request.auth),
            headers={"Cache-Control": "private, no-store"},
        )
