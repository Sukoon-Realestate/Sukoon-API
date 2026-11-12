from ..services.viewing_receipts import (
    execute_command,
    resolve_command,
    creation_receipt,
    read_command,
)
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from ..models import PropertyVisit
from ..serializers import (
    TenantVisitRequestDetailSerializer,
    OwnerVisitRequestDetailSerializer,
)
from ..services.viewing_access import can_read
from .post_visit_decision import PostVisitJsonRenderer


def visit_projection(visit, request):
    serializer = (
        OwnerVisitRequestDetailSerializer
        if visit.property.owner_id == request.user.pk
        else TenantVisitRequestDetailSerializer
    )
    return serializer(visit, context={"request": request}).data


class ViewingCommandAPIView(APIView):
    http_method_names = ["get", "post", "options"]
    name = "Viewing Command"
    permission_classes = [IsAuthenticated]
    renderer_classes = [PostVisitJsonRenderer]

    def get(self, request, id):
        data, code = read_command(
            request.user,
            id,
            request.query_params.get("request_key", ""),
            auth=request.auth,
            context={"request": request},
        )
        return Response(data, status=code)

    def post(self, request, id):
        visit = get_object_or_404(PropertyVisit, id=id)
        if not can_read(visit, request.user):
            raise NotFound()
        return execute_viewing_command(request, id, request.data)


def execute_viewing_command(request, id, payload):
    data, code = execute_command(
        request.user, id, payload, auth=request.auth, context={"request": request}
    )
    return Response(data, status=code)


def execute_visit_response(request, id, action):
    result = execute_viewing_command(request, id, {**request.data, "action": action})
    return Response(
        {
            **result.data["visit"],
            "operation": {
                key: result.data[key] for key in ("request_key", "action", "status")
            },
        },
        status=result.status_code,
    )


class ResolveViewingCommandAPIView(APIView):
    http_method_names = ["post", "options"]
    name = "Resolve Viewing Command"
    permission_classes = [IsAuthenticated]
    renderer_classes = [PostVisitJsonRenderer]

    def post(self, request, id):
        data, code = resolve_command(
            request.user,
            id,
            request.data,
            auth=request.auth,
            context={"request": request},
        )
        return Response(data, status=code)


class ViewingReceiptAPIView(APIView):
    http_method_names = ["get", "options"]
    name = "Viewing Receipt"
    permission_classes = [IsAuthenticated]
    renderer_classes = [PostVisitJsonRenderer]

    def get(self, request):
        data, code = creation_receipt(
            request.user,
            request.query_params.get("request_key", ""),
            auth=request.auth,
            context={"request": request},
        )
        return Response(data, status=code)
