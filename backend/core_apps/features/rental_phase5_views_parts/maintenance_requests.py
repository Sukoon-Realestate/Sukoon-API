"""Rental phase5 views: maintenance requests."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..renderers import FeatureJsonRenderer
from .maintenance_payload import _lease, maintenance_payload, _maintenance


class MaintenanceRequestsView(FeatureAPIView):
    name = "Maintenance Requests"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "maintenance_requests",
            "maintenance_requests",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "maintenance_requests",
            "maintenance_requests",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, lease_id):
        lease = _lease(request, lease_id, servicing=True)
        from ..services.maintenance_reads import collection_payload

        return Response(collection_payload(lease, request.user))

    def post(self, request, lease_id):
        lease = _lease(request, lease_id, servicing=True)
        from ..rental_serializers_parts.command_serializers import (
            MaintenanceCreateCommand,
            validated,
        )

        command = validated(MaintenanceCreateCommand, request.data)
        from ..services.personal_maintenance import create_request

        payload, status = create_request(
            request.user, request.auth, lease, command, request.data
        )
        return Response(payload, status=status)


# Stable callable import for integrations; URLs use the explicit class.
maintenance_requests = MaintenanceRequestsView.as_view()


class MaintenanceDetailView(FeatureAPIView):
    name = "Maintenance Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "maintenance_requests",
            "maintenance_detail",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, request_id):
        return Response(
            maintenance_payload(_maintenance(request, request_id), request.user)
        )


# Stable callable import for integrations; URLs use the explicit class.
maintenance_detail = MaintenanceDetailView.as_view()
