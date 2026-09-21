import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from core_apps.admin_api.permissions import IsAdminStaff
from core_apps.admin_api.serializers import (
    UserReportListSerializer,
    UserReportActionSerializer,
)
from core_apps.admin_api.services import get_reports_queryset, take_report_action
from core_apps.admin_api.filters import UserReportFilter

logger = logging.getLogger(__name__)


class AdminReportListAPIView(generics.ListAPIView):
    """
    Returns a paginated list of user reports and system-flagged violations.
    """

    permission_classes = [IsAdminStaff]
    serializer_class = UserReportListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserReportFilter

    def get_queryset(self):
        return get_reports_queryset()


class AdminReportActionAPIView(APIView):
    """
    Takes an administrative resolution on a user report.

    Request Body:
    {
        "action": "suspend_user",  // options: suspend_user, ban_user, dismiss, mark_active
        "notes": "تم إيقاف الحساب بعد التحقق من المحتوى المخالف"
    }
    """

    permission_classes = [IsAdminStaff]

    def post(self, request, report_id):
        serializer = UserReportActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        notes = serializer.validated_data.get("notes", "")

        report = take_report_action(
            report_id=report_id, action=action, reviewer=request.user, notes=notes
        )
        return Response(
            {"message": f"تم تطبيق الإجراء '{action}' على البلاغ بنجاح."},
            status=status.HTTP_200_OK,
        )
