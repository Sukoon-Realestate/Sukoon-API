import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from core_apps.common.locale_middleware import resolve_request_language
from core_apps.admin_api.permissions import IsPropertyReviewer
from core_apps.admin_api.serializers import (
    AdminPropertyItemSerializer,
    AdminPropertyActionSerializer,
)
from core_apps.admin_api.services import (
    get_admin_properties_queryset,
    get_admin_property_metrics,
    get_admin_property_detail,
)

logger = logging.getLogger(__name__)


class AdminPropertyListAPIView(generics.ListAPIView):
    """
    Returns a paginated list of properties with admin attributes and search/filter support.
    """

    permission_classes = [IsPropertyReviewer]
    serializer_class = AdminPropertyItemSerializer

    def get_queryset(self):
        status_param = self.request.query_params.get("status")
        type_param = self.request.query_params.get("property_type")
        search_param = self.request.query_params.get("search")
        return get_admin_properties_queryset(
            status=status_param,
            property_type=type_param,
            property_type_id=self.request.query_params.get("property_type_id"),
            search=search_param,
        )


class AdminPropertyMetricsAPIView(APIView):
    """
    Returns high-level property metrics (total, active, pending, rejected, acceptedToday, rejectedToday, openReports).
    """

    permission_classes = [IsPropertyReviewer]

    def get(self, request):
        metrics = get_admin_property_metrics(resolve_request_language(request))
        return Response(metrics, status=status.HTTP_200_OK)


class AdminPropertyDetailAPIView(APIView):
    """
    Returns full details of a specific property for administration.
    """

    permission_classes = [IsPropertyReviewer]

    def get(self, request, property_id):
        detail = get_admin_property_detail(property_id, reviewer=request.user)
        return Response(
            detail,
            status=status.HTTP_200_OK,
            headers={"Cache-Control": "private, no-store"},
        )


class AdminPropertyDecisionAPIView(APIView):
    permission_classes = [IsPropertyReviewer]
    action = None

    def post(self, request, property_id):
        from core_apps.common.idempotency import request_key, response_headers
        from core_apps.properties.services.moderation import decide

        serializer = AdminPropertyActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result, code, replayed = decide(
            property_id,
            reviewer=request.user,
            action=self.action,
            request_key=request_key(request),
            **serializer.validated_data,
        )
        return Response(result, status=code, headers=response_headers(replayed))


class AdminPropertyApproveAPIView(AdminPropertyDecisionAPIView):
    action = "approve"


class AdminPropertyRejectAPIView(AdminPropertyDecisionAPIView):
    action = "reject"


class AdminPropertyRevisionAPIView(AdminPropertyDecisionAPIView):
    action = "request_revision"


class AdminPropertyBlockAPIView(AdminPropertyDecisionAPIView):
    action = "block"


class AdminPropertyUnblockAPIView(AdminPropertyDecisionAPIView):
    action = "unblock"


class AdminPropertyReceiptAPIView(APIView):
    permission_classes = [IsPropertyReviewer]

    def get(self, request, property_id, key):
        from core_apps.properties.services.moderation import receipt

        return Response(
            receipt(request.user, property_id, str(key)),
            headers={"Cache-Control": "private, no-store"},
        )

    def post(self, request, property_id, key):
        from core_apps.properties.services.moderation import receipt

        return Response(
            receipt(
                request.user,
                property_id,
                str(key),
                close=True,
                auth_claims=request.auth,
            ),
            headers={"Cache-Control": "private, no-store"},
        )
