"""Visit: owner visit request reject apiview."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from core_apps.common.renderers import GenericJsonRenderer
from ...models import PropertyVisit
from ...serializers import OwnerVisitRejectSerializer
from ..viewing_commands import execute_visit_response


class OwnerVisitRequestRejectAPIView(generics.GenericAPIView):
    """
    API view for the owner to reject a pending visit request (Screen 3).

    Request Body Example (POST):
    {
        "reason": "timing_not_suitable",
        "custom_reason": "",
        "expected_revision": 1,
        "request_key": "original-request-uuid"
    }
    """

    serializer_class = OwnerVisitRejectSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        visit = get_object_or_404(
            PropertyVisit.objects.select_related(
                "tenant", "tenant__profile", "property"
            ),
            id=self.kwargs["id"],
            property__owner=request.user,
        )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return execute_visit_response(request, visit.id, "reject")


class OwnerVisitRequestAcceptAPIView(generics.GenericAPIView):
    """
    API view for the owner to accept a pending visit request (Screen 2 accept button).

    Request Body Example (POST):
    {"expected_revision": 1, "request_key": "original-request-uuid"}
    """

    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        visit = get_object_or_404(
            PropertyVisit.objects.select_related(
                "tenant", "tenant__profile", "property"
            ),
            id=self.kwargs["id"],
            property__owner=request.user,
        )
        return execute_visit_response(request, visit.id, "accept")
