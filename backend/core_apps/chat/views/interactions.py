from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core_apps.chat.models import Conversation
from core_apps.chat.services.group_access import authorize, eligible_participants
from core_apps.chat.services.group_projection import sender_payload
from core_apps.chat.services.group_rate_limit import enforce_rate
from core_apps.chat.services.reactions import set_reaction


class MessageReactionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id, message_id):
        enforce_rate(request.user, "reaction", maximum=120)
        return Response(
            set_reaction(
                get_object_or_404(Conversation, id=id),
                request.user,
                message_id,
                request.data,
            ),
            headers={"Cache-Control": "private, no-store"},
        )


class ConversationMembersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        conversation, _, _ = authorize(
            get_object_or_404(Conversation, id=id), request.user
        )
        if conversation.kind == "direct":
            raise NotFound()
        return Response(
            [
                sender_payload(p.user)
                for p in eligible_participants(conversation)
                .select_related("user", "user__profile")
                .order_by("user_id")
            ],
            headers={"Cache-Control": "private, no-store"},
        )
