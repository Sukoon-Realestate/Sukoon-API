"""Compatibility response for clients that used scheduled home reminders."""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer


class HomeVisitReminderAPIView(APIView):
    http_method_names = ["get", "options"]
    name = "Home Visit Reminder"
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request):
        response = Response({"banner": None})
        response["Cache-Control"] = "private, no-store"
        return response
