from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core_apps.chat.models import Conversation
from core_apps.chat.services.group_operations import (
    delete_group_message,
    set_preference,
)
from core_apps.chat.services.group_rate_limit import enforce_rate


class GroupMessageDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id, message_id):
        enforce_rate(request.user, "delete")
        return Response(
            delete_group_message(
                get_object_or_404(Conversation, id=id), request.user, message_id
            )
        )


class GroupPreferencesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        enforce_rate(request.user, "preferences")
        return Response(
            set_preference(
                get_object_or_404(Conversation, id=id),
                request.user,
                request.data.get("is_muted"),
            )
        )
