import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core_apps.admin_api.permissions import IsAdminStaff
from core_apps.admin_api.services import get_dashboard_overview_stats

logger = logging.getLogger(__name__)


class AdminDashboardStatsView(APIView):
    """
    Returns aggregated dashboard statistics, user distribution,
    growth charts, and recent platform activities.
    """

    permission_classes = [IsAdminStaff]

    def get(self, request):
        stats = get_dashboard_overview_stats()
        return Response(stats, status=status.HTTP_200_OK)
