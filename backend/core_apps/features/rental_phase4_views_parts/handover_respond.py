"""Rental phase4 views: handover respond."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import DepositAgreement
from ..renderers import FeatureJsonRenderer
from .handover_payload import _lease
from .lease_handovers import deposit_payload


class LeaseDepositView(FeatureAPIView):
    name = "Lease Deposit"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "handover_respond",
            "lease_deposit",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, lease_id):
        lease = _lease(request, lease_id)
        # Issuance belongs to the signing transaction. A read must not create a
        # separate charge, especially after the combined invoice was already paid.
        deposit = get_object_or_404(DepositAgreement, lease=lease)
        return Response(deposit_payload(deposit))


# Stable callable import for integrations; URLs use the explicit class.
lease_deposit = LeaseDepositView.as_view()


class HandoverRespondView(FeatureAPIView):
    name = "Handover Respond"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "handover_respond",
            "handover_respond",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, handover_id):
        from ..rental_serializers_parts.command_serializers import (
            HandoverRespondCommand,
            validated,
        )

        data = request.data if hasattr(request.data, "get") else {}
        action = data.get("action") or data.get("decision")
        if (
            not isinstance(action, str)
            or action not in {"accept", "dispute"}
            or not data.get("request_key")
        ):
            raise ValidationError(
                "accept/dispute, expected_revision, and request_key are required."
            )
        command = validated(HandoverRespondCommand, request.data)
        from ..services.handover_commands import respond_handover

        payload, status = respond_handover(
            request.user,
            request.auth,
            command,
            request.data,
            handover_id,
            action,
        )
        return Response(payload, status=status)


# Stable callable import for integrations; URLs use the explicit class.
handover_respond = HandoverRespondView.as_view()


from core_apps.features.services.money_projection import (
    payout_payload as payout_payload,
)


# Supported imports used by public facades and domain callers.
from ..services.payable_eligibility import (
    evaluate_owner_payables as evaluate_owner_payables,
)

__all__ = [
    "HandoverRespondView",
    "LeaseDepositView",
    "evaluate_owner_payables",
    "handover_respond",
    "lease_deposit",
    "payout_payload",
]
