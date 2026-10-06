import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from core_apps.admin_api.permissions import IsAdminStaff
from core_apps.admin_api.services.system_service import (
    get_system_health,
    get_audit_logs,
    get_push_campaigns,
    send_push_notification,
)

logger = logging.getLogger(__name__)


class AdminSystemHealthAPIView(APIView):
    """
    Returns system health indicators, server uptime, API performance stats, and admin notes.
    """

    permission_classes = [IsAdminStaff]

    def get(self, request):
        health_data = get_system_health()
        return Response(health_data, status=status.HTTP_200_OK)


class AdminAuditLogsAPIView(APIView):
    """
    Returns paginated audit activity logs.
    
    Query Params:
    - type: 'all' | 'kyc' | 'props' | 'users' | 'system'
    - search: str
    """

    permission_classes = [IsAdminStaff]
    pagination_class = PageNumberPagination

    def get(self, request):
        type_filter = request.query_params.get("type")
        search = request.query_params.get("search")

        logs = get_audit_logs(type_filter=type_filter, search=search)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(logs, request, view=self)
        if page is not None:
            return paginator.get_paginated_response(page)

        return Response({"results": logs, "count": len(logs)}, status=status.HTTP_200_OK)


class AdminPushCampaignsAPIView(APIView):
    """
    Returns list of sent push notification campaigns.
    """

    permission_classes = [IsAdminStaff]

    def get(self, request):
        campaigns = get_push_campaigns()
        return Response(campaigns, status=status.HTTP_200_OK)


class AdminSendPushNotificationAPIView(APIView):
    """
    Broadcasts or queues a new push notification campaign.
    
    Request body:
    {
        "title": "عروض الصيف",
        "body": "احجز زيارتك الآن",
        "audience": "all" | "tenants" | "landlords" | "verified"
    }
    """

    permission_classes = [IsAdminStaff]

    def post(self, request):
        title = request.data.get("title")
        body = request.data.get("body")
        audience = request.data.get("audience", "all")

        result = send_push_notification(title=title, body=body, audience=audience)
        return Response(result, status=status.HTTP_201_CREATED)
