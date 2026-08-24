import logging

from rest_framework import generics, permissions
from rest_framework.response import Response

from core_apps.common.renderers import GenericJsonRenderer

from ..serializers import OwnerDashboardSerializer
from ..services import OwnerDashboardService

logger = logging.getLogger(__name__)


class OwnerDashboardAPIView(generics.GenericAPIView):
    """
    API view to return the authenticated property owner's dashboard summary.

    Response includes the owner's profile header, key stats (weekly visits,
    active properties, overall rating, pending requests) and a list of pending
    visit requests awaiting the owner's response.
    """

    serializer_class = OwnerDashboardSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        dashboard_data = OwnerDashboardService.get_dashboard(owner=request.user)
        serializer = self.get_serializer(dashboard_data)
        return Response(serializer.data)
