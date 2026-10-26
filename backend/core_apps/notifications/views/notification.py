import logging
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.renderers import GenericJsonRenderer
from core_apps.notifications.serializers import (
    NotificationDetailSerializer,
    NotificationListSerializer,
)
from core_apps.notifications.services import NotificationService
from core_apps.notifications.services.inbox_scope import request_scope
from core_apps.profiles.serializers import UserSettingsSerializer
from core_apps.profiles.services import ProfileService

logger = logging.getLogger(__name__)


class NotificationListAPIView(generics.ListAPIView):
    """
    Screen: T-NOTIF-01 (الإشعارات - Notification List).

    GET: Returns a paginated list of notifications for the authenticated user.
    Optional query parameter: ?unread=true to filter for unread notifications only.
    """

    serializer_class = NotificationListSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from core_apps.notifications.services.preferences import touch
        touch(self.request.user, request_scope(self.request))
        unread_only = self.request.query_params.get("unread", "").lower() in (
            "true",
            "1",
        )
        return NotificationService.get_user_notifications(
            user=self.request.user,
            unread_only=unread_only,
            scope=request_scope(self.request),
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            # * Include unread count in response data
            response.data["unread_count"] = NotificationService.get_unread_count(
                request.user, scope=request_scope(request)
            )
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "unread_count": NotificationService.get_unread_count(
                    request.user, scope=request_scope(request)
                ),
                "results": serializer.data,
            }
        )


class NotificationDetailAPIView(generics.RetrieveAPIView):
    """
    Screen: T-NOTIF-02 (تفاصيل الإشعار - Notification Details).

    GET: Returns complete details of an in-app notification including structured
    appointment information and action buttons, and automatically marks it as read.
    """

    serializer_class = NotificationDetailSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        notification_id = self.kwargs.get("pk") or self.kwargs.get("id")
        return NotificationService.get_notification_detail(
            user=self.request.user, notification_id=notification_id
        )


class NotificationMarkReadAPIView(APIView):
    """
    PATCH: Marks a single notification as read.
    """

    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk, *args, **kwargs):
        notification = NotificationService.mark_as_read(
            user=request.user, notification_id=pk
        )
        serializer = NotificationDetailSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationMarkAllReadAPIView(APIView):
    """
    Screen: T-NOTIF-01 Header Button ('تحديد الكل كمقروء').

    POST: Marks all unread notifications for the authenticated user as read.
    """

    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        count = NotificationService.mark_all_as_read(
            request.user, scope=request_scope(request)
        )
        return Response(
            {
                "marked_count": count,
                "message": f"Marked {count} notifications as read.",
            },
            status=status.HTTP_200_OK,
        )


class NotificationUnreadCountAPIView(APIView):
    """
    GET: Returns the count of unread notifications for the authenticated user.
    """

    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        count = NotificationService.get_unread_count(
            request.user, scope=request_scope(request)
        )
        return Response({"unread_count": count}, status=status.HTTP_200_OK)


class NotificationSettingsAPIView(generics.RetrieveUpdateAPIView):
    """
    Screen: T-NOTIF-SETT (إعدادات الإشعارات).

    GET: Returns notification settings with 5 toggles and footer note.
    PATCH / PUT: Updates notification settings.
    """

    serializer_class = UserSettingsSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return ProfileService.get_user_settings(self.request.user)

    def retrieve(self, request, *args, **kwargs):
        from core_apps.notifications.services import preferences
        scope = request_scope(request)
        return Response(preferences.projection(
            preferences.get(request.user, scope), request.headers.get("Accept-Language", "ar")
        ))

    def update(self, request, *args, **kwargs):
        from core_apps.notifications.services import preferences
        return Response(preferences.projection(
            preferences.update(request, request_scope(request)),
            request.headers.get("Accept-Language", "ar"),
        ))
