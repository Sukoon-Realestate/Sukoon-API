import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from core_apps.admin_api.permissions import IsAdminStaff
from core_apps.admin_api.services.analytics_service import get_analytics_stats

logger = logging.getLogger(__name__)


class AdminAnalyticsStatsAPIView(APIView):
    """
    Returns analytics KPIs and breakdown charts for the specified period.
    
    Query Params:
    - period: 7 | 30 | 90 (default: 30)
    """

    permission_classes = [IsAdminStaff]

    def get(self, request):
        period_str = request.query_params.get("period", "30")
        try:
            period_days = int(period_str)
        except ValueError:
            period_days = 30

        stats = get_analytics_stats(period_days=period_days)
        return Response(stats, status=status.HTTP_200_OK)
