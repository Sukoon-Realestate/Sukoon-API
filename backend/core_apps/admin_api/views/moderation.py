import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from core_apps.admin_api.permissions import IsAdminStaff
from core_apps.admin_api.serializers.moderation_serializers import (
    ModerationItemSerializer,
    ModerationMetricsSerializer,
)
from core_apps.admin_api.services.moderation_service import (
    get_moderation_items_queryset,
    get_moderation_metrics,
    delete_moderation_item,
)

logger = logging.getLogger(__name__)


class AdminModerationListAPIView(generics.ListAPIView):
    """
    Returns a paginated list of properties requiring content moderation.
    """

    permission_classes = [IsAdminStaff]
    serializer_class = ModerationItemSerializer

    def get_queryset(self):
        return get_moderation_items_queryset()


class AdminModerationMetricsAPIView(APIView):
    """
    Returns aggregated metrics for suspicious and flagged content moderation.
    """

    permission_classes = [IsAdminStaff]

    def get(self, request):
        metrics = get_moderation_metrics()
        serializer = ModerationMetricsSerializer(metrics)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminModerationDeleteAPIView(APIView):
    """
    Hides/removes flagged content from the platform.
    """

    permission_classes = [IsAdminStaff]

    def post(self, request, property_id):
        delete_moderation_item(property_id, request.user)
        return Response(
            {"message": "تم حذف المحتوى المخالف بنجاح."},
            status=status.HTTP_200_OK,
        )
