from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from core_apps.chat.models import Conversation
from core_apps.chat.services.read_context import MessagePage
from core_apps.chat.services.group_access import authorize, visible_messages
from core_apps.chat.services import message_tools, quick_replies, polls
from core_apps.chat.services.forward_batch import forward_batch


def response(data):
    return Response(data, headers={"Cache-Control": "private, no-store"})


class MessageStarAPIView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["put", "options"]
    name = "message_star"

    def put(self, request, id, message_id):
        return response(
            message_tools.set_message_tool(
                get_object_or_404(Conversation, id=id),
                request.user,
                message_id,
                request.data,
            )
        )


class MessagePinAPIView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["put", "options"]
    name = "message_pin"

    def put(self, request, id, message_id):
        return response(
            message_tools.set_message_tool(
                get_object_or_404(Conversation, id=id),
                request.user,
                message_id,
                request.data,
                pin=True,
            )
        )


class StarredMessagesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "options"]
    name = "starred_messages"

    def get(self, request, id):
        conversation, participant, member = authorize(
            get_object_or_404(Conversation, id=id), request.user
        )
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
        prepared = MessagePage.prepare(
            page, (conversation, participant, member), request.query_params
        )
        result = pages.get_paginated_response([prepared.payload(m) for m in page])
        result["Cache-Control"] = "private, no-store"
        return result


class MessageReadersAPIView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "options"]
    name = "message_readers"

    def get(self, request, id, message_id):
        message, rows = message_tools.message_readers(
            get_object_or_404(Conversation, id=id), request.user, message_id
        )
        pages = PageNumberPagination()
        pages.page_size = 20
        page = pages.paginate_queryset(rows, request)
        receipts = {
            (row.user_id, row.membership_period): row
            for row in message.read_receipts.filter(
                user_id__in=[reader.user_id for reader in page]
            )
        }
        result = pages.get_paginated_response(
            [
                message_tools.reader_payload(message, reader, receipts=receipts)
                for reader in page
            ]
        )
        result["Cache-Control"] = "private, no-store"
        return result


class SavedRepliesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "options"]
    name = "saved_replies"

    def get(self, request):
        return response({"replies": quick_replies.listing(request.user)})


class SavedReplyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["put", "delete", "options"]
    name = "saved_reply"

    def put(self, request, id):
        return response(
            quick_replies.save(
                request.user, id, request.data if request.method == "PUT" else None
            )
        )

    def delete(self, request, id):
        return response(
            quick_replies.save(
                request.user, id, request.data if request.method == "PUT" else None
            )
        )


class PollVoteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["put", "options"]
    name = "poll_vote"

    def put(self, request, id, message_id):
        return response(
            polls.change_poll(
                get_object_or_404(Conversation, id=id),
                request.user,
                message_id,
                request.data,
            )
        )


class PollCloseAPIView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["post", "options"]
    name = "poll_close"

    def post(self, request, id, message_id):
        return response(
            polls.change_poll(
                get_object_or_404(Conversation, id=id),
                request.user,
                message_id,
                request.data,
                close=True,
            )
        )


class ForwardMessagesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["post", "options"]
    name = "forward_messages"

    def post(self, request, id):
        return response(
            forward_batch(
                get_object_or_404(Conversation, id=id), request.user, request.data
            )
        )
