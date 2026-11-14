from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.chat.models import Conversation
from core_apps.chat.services.forwarding import (
    destinations,
    destination_page,
    forward_message,
)
from core_apps.chat.services.group_access import authorize
from core_apps.chat.services.group_projection import message_payload


class ForwardDestinationsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "options"]
    name = "forward_destinations"

    def get(self, request, id, message_id):
        bounded = request.query_params.get("bounded", "false")
        if bounded not in {"true", "false"}:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"bounded": "Use true or false."})
        if bounded == "true" or "cursor" in request.query_params:
            return Response(
                destination_page(
                    get_object_or_404(Conversation, id=id),
                    request.user,
                    message_id,
                    request.query_params,
                ),
                headers={"Cache-Control": "private, no-store"},
            )
        rows = destinations(
            get_object_or_404(Conversation, id=id),
            request.user,
            message_id,
            request.query_params,
        )
        pagination = PageNumberPagination()
        pagination.page_size = 20
        page = pagination.paginate_queryset(rows, request)
        response = pagination.get_paginated_response(page)
        response["Cache-Control"] = "private, no-store"
        return response


class ForwardAPIView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["post", "options"]
    name = "forward"

    def post(self, request, id, message_id):
        message = forward_message(
            get_object_or_404(Conversation, id=id),
            request.user,
            message_id,
            request.data,
        )
        _, participant, member = authorize(message.conversation, request.user)
        return Response(
            message_payload(message, participant, member),
            headers={"Cache-Control": "private, no-store"},
        )
