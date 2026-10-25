from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from core_apps.chat.models import Conversation
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.mention_navigation import navigation_payload, see_mention


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unread_mentions(request, id):
    conversation, participant, _ = authorize(get_object_or_404(Conversation, id=id), request.user)
    if conversation.kind == "direct":
        raise NotFound()
    return Response(navigation_payload(conversation, participant), headers={"Cache-Control": "private, no-store"})


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def mention_seen(request, id, message_id):
    return Response(
        see_mention(
            get_object_or_404(Conversation, id=id), request.user, message_id, request.data.get("membership_period")
        ),
        headers={"Cache-Control": "private, no-store"},
    )
