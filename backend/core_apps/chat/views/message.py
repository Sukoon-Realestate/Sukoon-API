import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.chat.models import Conversation, Message
from core_apps.chat.permissions import IsParticipant
from core_apps.chat.serializers import MessageCreateSerializer, MessageSerializer
from core_apps.chat.services.message_service import send_message

logger = logging.getLogger(__name__)


class _MessagePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class MessageListAPIView(ListAPIView):
    """List message history for a conversation, ordered oldest-first."""

    permission_classes = [IsAuthenticated, IsParticipant]
    serializer_class = MessageSerializer
    pagination_class = _MessagePagination

    def get_object(self):
        conversation = get_object_or_404(Conversation, id=self.kwargs["id"])
        self.check_object_permissions(self.request, conversation)
        return conversation

    def get_queryset(self):
        conversation = self.get_object()
        return (
            Message.objects.filter(conversation=conversation)
            .select_related("sender", "sender__profile")
            .order_by("created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class MessageCreateAPIView(APIView):
    """
    Send a message in a conversation (REST fallback — ws path is preferred).

    Request body:
        {"content": "Hello, is this property still available?"}
    """

    permission_classes = [IsAuthenticated, IsParticipant]

    def post(self, request, id):
        conversation = get_object_or_404(Conversation, id=id)
        self.check_object_permissions(request, conversation)

        serializer = MessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message = send_message(
            conversation=conversation,
            sender=request.user,
            content=serializer.validated_data["content"],
        )
        return Response(
            MessageSerializer(message, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
