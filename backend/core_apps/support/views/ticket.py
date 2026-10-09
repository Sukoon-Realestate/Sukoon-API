import logging
from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.renderers import GenericJsonRenderer
from core_apps.support.models import Ticket
from core_apps.support.pagination import SupportPagination
from core_apps.support.serializers import (
    TicketCreateSerializer,
    TicketDetailSerializer,
    TicketListSerializer,
    TicketReplySerializer,
)
from core_apps.support.services import (
    TicketClosedConflict,
    add_ticket_reply,
    create_ticket,
    get_ticket_detail,
    list_user_tickets,
)

logger = logging.getLogger(__name__)


class TicketListCreateAPIView(generics.ListCreateAPIView):
    """
    GET support/tickets/?workspace=tenant&page=1&page_size=20
    List tickets belonging to authenticated user and specified workspace.

    POST support/tickets/
    Create a new support ticket with initial message and optional attachments.
    Accepts application/json or multipart/form-data.
    """

    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]
    pagination_class = SupportPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TicketCreateSerializer
        return TicketListSerializer

    def get_queryset(self):
        workspace = self.request.query_params.get("workspace", "tenant")
        return list_user_tickets(user=self.request.user, workspace=workspace)

    def create(self, request, *args, **kwargs) -> Response:
        serializer = TicketCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attachments = request.FILES.getlist("attachments")

        ticket = create_ticket(
            user=request.user,
            workspace=serializer.validated_data["workspace"],
            category=serializer.validated_data["category"],
            subject=serializer.validated_data["subject"],
            description=serializer.validated_data["description"],
            attachments=attachments,
            rental_context=serializer.validated_data.get("rental_context", {}),
        )

        detail_serializer = TicketDetailSerializer(ticket, context={"request": request})
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class TicketDetailAPIView(generics.RetrieveAPIView):
    """
    GET support/tickets/{id}/?workspace=owner
    Retrieves full ticket conversation history and attachments.
    Enforces account ownership and workspace scoping.
    """

    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]
    serializer_class = TicketDetailSerializer

    def get_object(self) -> Ticket:
        ticket_id = self.kwargs["id"]
        workspace = self.request.query_params.get("workspace")
        try:
            return get_ticket_detail(
                user=self.request.user,
                ticket_id=ticket_id,
                workspace=workspace,
            )
        except Ticket.DoesNotExist:
            raise Http404("Ticket not found or access denied.")


class TicketReplyAPIView(APIView):
    """
    POST support/tickets/{id}/replies/
    Appends a reply from the authenticated user to the ticket thread.
    Returns the complete updated ticket.
    Rejects replies to resolved/closed tickets with 409 Conflict.
    """

    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request, id, *args, **kwargs) -> Response:
        serializer = TicketReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        workspace = request.query_params.get("workspace")
        try:
            updated_ticket = add_ticket_reply(
                user=request.user,
                ticket_id=id,
                body=serializer.validated_data["body"],
                workspace=workspace,
            )
        except TicketClosedConflict as exc:
            return Response(
                {"message": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        except Ticket.DoesNotExist:
            raise Http404("Ticket not found or access denied.")

        detail_serializer = TicketDetailSerializer(
            updated_ticket, context={"request": request}
        )
        return Response(detail_serializer.data, status=status.HTTP_200_OK)
