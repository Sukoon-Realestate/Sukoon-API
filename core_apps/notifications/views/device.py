import logging
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.renderers import GenericJsonRenderer
from core_apps.notifications.serializers import (
    DeviceTokenSerializer,
    DeviceTokenUnregisterSerializer,
)
from core_apps.notifications.services import NotificationService

logger = logging.getLogger(__name__)


class DeviceTokenCreateAPIView(APIView):
    """
    POST: Register or update an FCM device token for push notifications.

    Request Body Example:
    {
        "token": "fcm_device_token_string...",
        "device_type": "android",  // android | ios | web
        "device_name": "Pixel 7 Pro" // optional
    }
    """

    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = DeviceTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        device_type = serializer.validated_data.get("device_type", "android")
        device_name = serializer.validated_data.get("device_name", "")

        device = NotificationService.register_device_token(
            user=request.user,
            token=token,
            device_type=device_type,
            device_name=device_name,
        )

        response_serializer = DeviceTokenSerializer(device)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class DeviceTokenDeleteAPIView(APIView):
    """
    POST / DELETE: Unregister/deactivate an FCM device token (e.g., on logout).

    Request Body Example:
    {
        "token": "fcm_device_token_string..."
    }
    """

    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return self._handle_unregister(request)

    def delete(self, request, *args, **kwargs):
        return self._handle_unregister(request)

    def _handle_unregister(self, request):
        serializer = DeviceTokenUnregisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        NotificationService.unregister_device_token(user=request.user, token=token)

        return Response(
            {"message": "Device token unregistered successfully."},
            status=status.HTTP_200_OK,
        )
