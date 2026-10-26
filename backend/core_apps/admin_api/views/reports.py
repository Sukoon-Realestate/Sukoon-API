from core_apps.admin_api.permissions import IsSupportStaff
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

        take_report_action(
            report_id=report_id, action=action, reviewer=request.user, notes=notes
        )
        return Response(
            {"message": f"تم تطبيق الإجراء '{action}' على البلاغ بنجاح."},
            status=status.HTTP_200_OK,
        )


class AdminReportMetricsAPIView(APIView):
    """
    Returns aggregated counts for user reports by status.
    """

    permission_classes = [IsAdminStaff]

    def get(self, request):
        from core_apps.admin_api.services.report_service import get_report_metrics
        data = get_report_metrics()
        return Response(data, status=status.HTTP_200_OK)


class AdminSupportTicketsListAPIView(generics.ListAPIView):
    """
    Returns a paginated list of support tickets with optional tab filter.
    
    Query Params:
    - tab: all | high | landlord | tenant
    """

    permission_classes = [IsSupportStaff]
    serializer_class = None

    def get_serializer_class(self):
        from core_apps.admin_api.serializers.report_serializers import SupportTicketSerializer
        return SupportTicketSerializer

    def get_queryset(self):
        from core_apps.admin_api.services.report_service import get_support_tickets_queryset
        qs = get_support_tickets_queryset()
        
        tab = self.request.query_params.get("tab")
        if tab == "high":
            qs = qs.filter(escalated=True, status__in=["open", "in_progress"])
        elif tab == "landlord":
            qs = qs.filter(workspace="owner")
        elif tab == "tenant":
            qs = qs.exclude(workspace__in=["owner", "account"])
            
        return qs


class AdminSupportMetricsAPIView(APIView):
    """
    Returns live operational metrics for support tickets.
    """

    permission_classes = [IsSupportStaff]

    def get(self, request):
        from core_apps.admin_api.services.report_service import get_support_metrics
        data = get_support_metrics()
        return Response(data, status=status.HTTP_200_OK)


class AdminReportsOverviewAPIView(APIView):
    """
    Returns comprehensive overview stats including dispute distributions,
    recent bookings, and high-level ticket counts.
    """

    permission_classes = [IsAdminStaff]

    def get(self, request):
        from core_apps.admin_api.services.report_service import (
            get_reports_overview_stats,
            get_reports_queryset,
        )
        from core_apps.admin_api.serializers.report_serializers import OverviewTicketSerializer

        stats = get_reports_overview_stats()
        
        # ? Get recent tickets for the table
        recent_tickets_qs = get_reports_queryset()[:20]
        serializer = OverviewTicketSerializer(recent_tickets_qs, many=True)
        
        return Response(
            {
                "measured_at": stats["measured_at"],
                "metrics": {
                    "avgResolutionTime": stats["avgResolutionTime"],
                    "activeDisputes": stats["activeDisputes"],
                    "solvedToday": stats["solvedToday"],
                    "openTickets": stats["openTickets"],
                },
                "tickets": serializer.data,
                "disputeReasons": stats["disputeReasons"],
                "bookingLog": stats["bookingLog"],
            },
            status=status.HTTP_200_OK,
        )

