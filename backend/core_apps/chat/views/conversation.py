import logging

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.chat.models import Conversation
from core_apps.chat.permissions import IsParticipant
from core_apps.chat.serializers import (
    ConversationCreateSerializer,
    ConversationSerializer,
)
from core_apps.chat.services.message_service import (
    get_or_create_direct_conversation,
    mark_conversation_read,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class _ConversationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ConversationListAPIView(ListAPIView):
    """List conversations for the authenticated user, ordered by most-recent message."""

    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer
    pagination_class = _ConversationPagination

    def get_queryset(self):
        if 'workspace' in self.request.query_params:
            from core_apps.chat.services.workspace_inbox import scoped
            return scoped(self.request.user, self.request.query_params['workspace'], self.request.query_params.get('company_id', '')).prefetch_related('participants__profile', 'participant_set').order_by('-last_message_at', '-id')
        queryset = (
            Conversation.objects.filter(participant_set__user=self.request.user)
            .prefetch_related("participants__profile", "participant_set")
            .order_by("-last_message_at")
        )
        if self.request.query_params.get("include_groups") != "true":
            return queryset.filter(kind="direct")
        from django.db.models import Q, F
        from rest_framework.exceptions import APIException
        from core_apps.features.services.planning import require_planning

        try:
            require_planning(self.request.user, "housing_groups")
        except APIException:
            return queryset.filter(kind="direct")
        return queryset.filter(
            Q(kind="direct")
            | Q(
                kind="housing_group",
                housing_group__status="active",
                participant_set__user=self.request.user,
                participant_set__membership__status="active",
                participant_set__membership_revision=F(
                    "participant_set__membership__joined_revision"
                ),
            )
        ).distinct()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class ConversationCreateAPIView(APIView):
    """
    Start or retrieve a direct (1:1) conversation.

    Request body:
        {"user_id": "<uuid>"}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ConversationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        other = get_object_or_404(User, id=serializer.validated_data["user_id"])
        conversation = get_or_create_direct_conversation(
            user=request.user, other_user=other
        )
        workspace = serializer.validated_data.get('workspace')
        if workspace:
            from core_apps.chat.models import ConversationWorkspace
            ConversationWorkspace.objects.get_or_create(conversation=conversation, user=request.user, workspace=workspace)
        return Response(
            ConversationSerializer(conversation, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class ConversationDetailAPIView(APIView):
    """Return fresh participant/contact metadata to conversation members only."""

    permission_classes = [IsAuthenticated, IsParticipant]

    def get(self, request, id):
        conversation = get_object_or_404(
            Conversation.objects.prefetch_related(
                "participants__profile", "participant_set"
            ),
            id=id,
        )
        if conversation.kind in {"housing_group", "company_request"}:
            from core_apps.chat.services.group_projection import summary

            return Response(summary(conversation, request.user))
        self.check_object_permissions(request, conversation)
        return Response(
            ConversationSerializer(conversation, context={"request": request}).data
        )


class ConversationReadAPIView(APIView):
    """
    Mark a conversation as read for the requesting user.

    Resets unread_count to 0 and broadcasts a read receipt to other participants.
    """

    permission_classes = [IsAuthenticated, IsParticipant]

    def post(self, request, id):
        conversation = get_object_or_404(Conversation, id=id)
        if (
            conversation.kind in {"housing_group", "company_request"}
            or "last_read_sequence" in request.data
        ):
            from core_apps.chat.services.group_operations import mark_group_read

            return Response(
                mark_group_read(
                    conversation, request.user, request.data.get("last_read_sequence")
                )
            )
        self.check_object_permissions(request, conversation)
        mark_conversation_read(conversation=conversation, user=request.user)
        return Response({"status": "read"}, status=status.HTTP_200_OK)
