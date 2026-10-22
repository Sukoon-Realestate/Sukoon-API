import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from core_apps.admin_api.permissions import IsSystemOwner
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

    permission_classes = [IsSystemOwner]

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

    permission_classes = [IsSystemOwner]
    pagination_class = PageNumberPagination

    def get(self, request):
        type_filter = request.query_params.get("type")
        search = request.query_params.get("search")

        logs = get_audit_logs(type_filter=type_filter, search=search)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(logs, request, view=self)
        if page is not None:
            return paginator.get_paginated_response(page)

        return Response(
            {"results": logs, "count": len(logs)}, status=status.HTTP_200_OK
        )


class AdminPushCampaignsAPIView(APIView):
    """
    Returns list of sent push notification campaigns.
    """

    permission_classes = [IsSystemOwner]

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

    permission_classes = [IsSystemOwner]

    def post(self, request):
        title = request.data.get("title")
        body = request.data.get("body")
        audience = request.data.get("audience", "all")

        result = send_push_notification(title=title, body=body, audience=audience)
        return Response(result, status=status.HTTP_201_CREATED)


class AdminCampaignPreviewAPIView(APIView):
    permission_classes = [IsSystemOwner]

    def post(self, request):
        from core_apps.admin_api.services.push_campaigns import preview, payload
        return Response(payload(preview(request.user, request.data)), status=201)


class AdminCampaignDetailAPIView(APIView):
    permission_classes = [IsSystemOwner]

    def get(self, request, campaign_id):
        from django.shortcuts import get_object_or_404
        from core_apps.admin_api.models import PushCampaign
        from core_apps.admin_api.services.push_campaigns import payload
        return Response(payload(get_object_or_404(PushCampaign, id=campaign_id)))

    def post(self, request, campaign_id):
        from core_apps.admin_api.services.push_campaigns import transition, payload
        from rest_framework.exceptions import ValidationError
        if request.data.get("action") not in {"confirm", "cancel"}:
            raise ValidationError({"action": "Choose confirm or cancel."})
        return Response(payload(transition(request.user, campaign_id, request.data, cancel=request.data["action"] == "cancel")))
