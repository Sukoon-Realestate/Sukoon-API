from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.common.idempotency import request_key
from ..services.dated_closures import manage_dated_closures


class AvailabilityClosuresAPIView(APIView):
    http_method_names = ["get", "post", "put", "options"]
    name = "Availability Closures"
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request, property_id):
        data, code = manage_dated_closures(
            request.user, property_id, {}, method="GET", auth=request.auth
        )
        return Response(
            data, status=code, headers={"Cache-Control": "private, no-store"}
        )

    def post(self, request, property_id):
        data, code = manage_dated_closures(
            request.user, property_id, request.data, method="POST", auth=request.auth
        )
        return Response(
            data, status=code, headers={"Cache-Control": "private, no-store"}
        )

    def put(self, request, property_id):
        data, code = manage_dated_closures(
            request.user,
            property_id,
            request.data,
            method="PUT",
            auth=request.auth,
            idempotency_key=request_key(request),
        )
        return Response(
            data, status=code, headers={"Cache-Control": "private, no-store"}
        )
