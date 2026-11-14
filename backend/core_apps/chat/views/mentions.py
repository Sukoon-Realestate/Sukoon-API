from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from core_apps.chat.models import Conversation
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.mention_navigation import navigation_payload, see_mention


class UnreadMentionsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "options"]
    name = "unread_mentions"

    def get(self, request, id):
        conversation, participant, _ = authorize(
            get_object_or_404(Conversation, id=id), request.user
        )
        if conversation.kind == "direct":
            raise NotFound()
        return Response(
            navigation_payload(conversation, participant),
            headers={"Cache-Control": "private, no-store"},
        )


class MentionSeenAPIView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["put", "options"]
    name = "mention_seen"

    def put(self, request, id, message_id):
        from core_apps.common.command_fields import require_object_body
        require_object_body(request)
        return Response(
            see_mention(
                get_object_or_404(Conversation, id=id),
                request.user,
                message_id,
                request.data.get("membership_period"),
            ),
            headers={"Cache-Control": "private, no-store"},
        )
