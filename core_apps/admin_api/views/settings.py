import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from core_apps.admin_api.permissions import IsAdminStaff
from core_apps.admin_api.services.settings_service import (
    get_platform_settings,
    update_platform_settings,
)

logger = logging.getLogger(__name__)


class AdminPlatformSettingsAPIView(APIView):
    """
    Returns and updates platform general rules and verification settings.
    """

    permission_classes = [IsAdminStaff]

    def get(self, request):
        settings_data = get_platform_settings()
        return Response(settings_data, status=status.HTTP_200_OK)

    def post(self, request):
        updated = update_platform_settings(request.data)
        return Response(updated, status=status.HTTP_200_OK)
