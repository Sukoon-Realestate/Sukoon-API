from ..services.viewing_message_context_commands import message_context
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer


class ViewingMessageContextAPIView(APIView):
    http_method_names = ["get", "options"]
    name = "Viewing Message Context"
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request, visit_id):
        data, code = message_context(
            request.user,
            visit_id,
            {},
            method="GET",
            auth=request.auth,
            expected_revision=request.query_params.get("expected_revision"),
        )
        return Response(
            data, status=code, headers={"Cache-Control": "private, no-store"}
        )
