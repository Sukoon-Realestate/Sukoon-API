from ..services.viewing_times_commands import manage_time_proposals
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer


class ViewingTimesAPIView(APIView):
    http_method_names = ["get", "post", "options"]
    name = "Viewing Times"
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request, visit_id):
        data, code = manage_time_proposals(
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

    def post(self, request, visit_id):
        data, code = manage_time_proposals(
            request.user,
            visit_id,
            request.data,
            method="POST",
            auth=request.auth,
            expected_revision=request.query_params.get("expected_revision"),
        )
        return Response(
            data, status=code, headers={"Cache-Control": "private, no-store"}
        )
