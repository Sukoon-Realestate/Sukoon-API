"""Authenticated OS actions target the delivered message."""

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core_apps.chat.services.notification_actions import apply_notification_action


class ActionBody(serializers.Serializer):
    notification_id = serializers.UUIDField()
    recipient_id = serializers.UUIDField()
    membership_period = serializers.UUIDField()
    action = serializers.ChoiceField(choices=["reply", "mark_read"])
    client_message_id = serializers.UUIDField()
    content = serializers.CharField(
        required=False, allow_blank=True, max_length=4000, trim_whitespace=False
    )


class NotificationActionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["post", "options"]
    name = "notification_action"

    def post(self, request):
        body = ActionBody(data=request.data)
        body.is_valid(raise_exception=True)
        return Response(
            apply_notification_action(request.user, body.validated_data),
            headers={"Cache-Control": "private, no-store"},
        )
