import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from core_apps.admin_api.permissions import IsAdminStaff
from core_apps.admin_api.serializers import (
    AdminPropertyItemSerializer,
    AdminPropertyActionSerializer,
)
from core_apps.admin_api.services import (
    get_admin_properties_queryset,
    get_admin_property_metrics,
    get_admin_property_detail,
    approve_admin_property,
    reject_admin_property,
    request_admin_property_revision,
)

logger = logging.getLogger(__name__)


class AdminPropertyListAPIView(generics.ListAPIView):
    """
    Returns a paginated list of properties with admin attributes and search/filter support.
    """

    permission_classes = [IsAdminStaff]
    serializer_class = AdminPropertyItemSerializer

    def get_queryset(self):
        status_param = self.request.query_params.get("status")
        type_param = self.request.query_params.get("property_type")
        search_param = self.request.query_params.get("search")
        return get_admin_properties_queryset(
            status=status_param, property_type=type_param, search=search_param
        )


class AdminPropertyMetricsAPIView(APIView):
    """
    Returns high-level property metrics (total, active, pending, rejected, acceptedToday, rejectedToday, openReports).
    """

    permission_classes = [IsAdminStaff]

    def get(self, request):
        metrics = get_admin_property_metrics()
        return Response(metrics, status=status.HTTP_200_OK)


class AdminPropertyDetailAPIView(APIView):
    """
    Returns full details of a specific property for administration.
    """

    permission_classes = [IsAdminStaff]

    def get(self, request, property_id):
        detail = get_admin_property_detail(property_id)
        return Response(detail, status=status.HTTP_200_OK)


class AdminPropertyApproveAPIView(APIView):
    """
    Approves and verifies a property listing.
    """

    permission_classes = [IsAdminStaff]

    def post(self, request, property_id):
        prop = approve_admin_property(property_id)
        return Response(
            {"message": f"تمت الموافقة على إدراج العقار '{prop.title}' وتفعيله بنجاح."},
            status=status.HTTP_200_OK,
        )


class AdminPropertyRejectAPIView(APIView):
    """
    Rejects and hides a property listing.
    """

    permission_classes = [IsAdminStaff]

    def post(self, request, property_id):
        serializer = AdminPropertyActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("reason", "")
        prop = reject_admin_property(property_id, reason=reason)
        return Response(
            {"message": f"تم رفض إدراج العقار '{prop.title}' بنجاح."},
            status=status.HTTP_200_OK,
        )


class AdminPropertyRevisionAPIView(APIView):
    """
    Requests revisions from the owner for a property listing.
    """

    permission_classes = [IsAdminStaff]

    def post(self, request, property_id):
        serializer = AdminPropertyActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("reason", "")
        prop = request_admin_property_revision(property_id, reason=reason)
        return Response(
            {"message": f"تم إرسال طلب تعديل البيانات لمالك العقار '{prop.title}'."},
            status=status.HTTP_200_OK,
        )
