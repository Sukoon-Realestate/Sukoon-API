from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from core_apps.chat.models import Conversation
from core_apps.chat.services.group_access import authorize, visible_messages
from core_apps.chat.services.group_projection import message_payload
from core_apps.chat.services import message_tools, quick_replies, polls
from core_apps.chat.services.forward_batch import forward_batch


def response(data):
    return Response(data, headers={"Cache-Control": "private, no-store"})


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def message_star(request, id, message_id):
    return response(
        message_tools.set_message_tool(get_object_or_404(Conversation, id=id), request.user, message_id, request.data)
    )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def message_pin(request, id, message_id):
    return response(
        message_tools.set_message_tool(
            get_object_or_404(Conversation, id=id), request.user, message_id, request.data, pin=True
        )
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def starred_messages(request, id):
    conversation, participant, member = authorize(get_object_or_404(Conversation, id=id), request.user)
    rows = (
        visible_messages(conversation, participant)
        .filter(
            deleted_at__isnull=True,
            stars__user=request.user,
            stars__membership_period=participant.membership_period,
            stars__enabled=True,
        )
        .order_by("-sequence")
    )
    pages = PageNumberPagination()
    pages.page_size = 20
    page = pages.paginate_queryset(rows, request)
    result = pages.get_paginated_response([message_payload(m, participant, member) for m in page])
    result["Cache-Control"] = "private, no-store"
    return result


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def message_readers(request, id, message_id):
    message, rows = message_tools.message_readers(get_object_or_404(Conversation, id=id), request.user, message_id)
    pages = PageNumberPagination()
    pages.page_size = 20
    page = pages.paginate_queryset(rows, request)
    result = pages.get_paginated_response([message_tools.reader_payload(message, reader) for reader in page])
    result["Cache-Control"] = "private, no-store"
    return result


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def saved_replies(request):
    return response({"replies": quick_replies.listing(request.user)})


@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def saved_reply(request, id):
    return response(quick_replies.save(request.user, id, request.data if request.method == "PUT" else None))


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def poll_vote(request, id, message_id):
    return response(polls.change_poll(get_object_or_404(Conversation, id=id), request.user, message_id, request.data))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def poll_close(request, id, message_id):
    return response(
        polls.change_poll(get_object_or_404(Conversation, id=id), request.user, message_id, request.data, close=True)
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def forward_messages(request, id):
    return response(forward_batch(get_object_or_404(Conversation, id=id), request.user, request.data))
