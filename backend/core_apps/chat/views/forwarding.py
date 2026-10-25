from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.chat.models import Conversation
from core_apps.chat.services.forwarding import destinations, forward_message
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.group_projection import message_payload


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def forward_destinations(request, id, message_id):
    rows = destinations(get_object_or_404(Conversation, id=id), request.user, message_id, request.query_params)
    pagination = PageNumberPagination()
    pagination.page_size = 20
    page = pagination.paginate_queryset(rows, request)
    response = pagination.get_paginated_response(page)
    response["Cache-Control"] = "private, no-store"
    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def forward(request, id, message_id):
    message = forward_message(get_object_or_404(Conversation, id=id), request.user, message_id, request.data)
    _, participant, member = authorize(message.conversation, request.user)
    return Response(message_payload(message, participant, member), headers={"Cache-Control": "private, no-store"})
