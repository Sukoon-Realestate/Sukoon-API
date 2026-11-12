from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.common.idempotency import request_key
from ..services.hidden_preferences import read_preferences, update_preference


class HiddenListingsAPIView(APIView):
    http_method_names = ["get", "post", "options"]
    name = "Hidden Listings"
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def check_workspace(self, request):
        if request.headers.get("X-Sukoon-Company-Id") or request.query_params.get(
            "workspace", "individual"
        ) not in {"individual", "owner"}:
            raise PermissionDenied("Use individual or owner search preferences.")

    def get(self, request):
        self.check_workspace(request)
        return Response(
            read_preferences(request.user, request.query_params.get("property_id")),
            headers={"Cache-Control": "private, no-store"},
        )

    def post(self, request):
        self.check_workspace(request)
        data, code = update_preference(
            request.user,
            request.data,
            auth=request.auth,
            idempotency_key=request_key(request),
        )
        return Response(
            data, status=code, headers={"Cache-Control": "private, no-store"}
        )
