"""Rental phase4 views: lease handovers."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..renderers import FeatureJsonRenderer
from .handover_payload import _money, _lease, handover_payload, _handover


class LeaseHandoversView(FeatureAPIView):
    name = "Lease Handovers"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    parser_classes = [JSONParser]
    action_policies = {
        "get": ActionPolicy(
            "lease_handovers",
            "lease_handovers",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "lease_handovers",
            "lease_handovers",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, lease_id):
        lease = _lease(request, lease_id)
        items = [
            handover_payload(x, request.user)
            for x in lease.handovers.prefetch_related("evidence").all()
        ]
        return Response(
            {"count": len(items), "next": None, "previous": None, "results": items}
        )

    def post(self, request, lease_id):
        lease = _lease(request, lease_id)
        from ..rental_serializers_parts.command_serializers import (
            HandoverCreateCommand,
            validated,
        )

        command = validated(HandoverCreateCommand, request.data)
        from ..services.handover_commands import create_handover

        payload, status = create_handover(
            request.user, request.auth, command, request.data, lease, lease_id
        )
        return Response(payload, status=status)


# Stable callable import for integrations; URLs use the explicit class.
lease_handovers = LeaseHandoversView.as_view()


class HandoverDetailView(FeatureAPIView):
    name = "Handover Detail"
    http_method_names = ["get", "patch", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "lease_handovers",
            "handover_detail",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "patch": ActionPolicy(
            "lease_handovers",
            "handover_detail",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, handover_id):
        handover = _handover(request, handover_id)
        return Response(handover_payload(handover, request.user))

    def patch(self, request, handover_id):
        handover = _handover(request, handover_id)
        from ..rental_serializers_parts.command_serializers import (
            HandoverUpdateCommand,
            validated,
        )

        command = validated(HandoverUpdateCommand, request.data)
        from ..services.handover_commands import update_handover

        payload, status = update_handover(
            request.user, request.auth, command, request.data, handover, handover_id
        )
        return Response(payload, status=status)


# Stable callable import for integrations; URLs use the explicit class.
handover_detail = HandoverDetailView.as_view()


def deposit_payload(deposit):
    remaining = max(
        deposit.collected_minor - deposit.returned_minor - deposit.applied_minor, 0
    )
    return {
        "id": str(deposit.id),
        "lease_id": str(deposit.lease.id),
        "revision": deposit.revision,
        "holder": deposit.lease.terms.get("deposit_holder", "platform"),
        "invoice_id": str(deposit.invoice.id) if deposit.invoice else None,
        "status": "collected" if deposit.collected_minor else "due",
        "agreed": _money(deposit.agreed_minor),
        "due": _money(deposit.due_minor),
        "collected": _money(deposit.collected_minor),
        "returned": _money(deposit.returned_minor),
        "applied": _money(deposit.applied_minor),
        "disputed": _money(deposit.disputed_minor),
        "remaining": _money(remaining),
    }
