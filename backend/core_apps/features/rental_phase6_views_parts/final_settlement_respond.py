"""Rental phase6 views: final settlement respond."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..renderers import FeatureJsonRenderer


class FinalSettlementRespondView(FeatureAPIView):
    name = "Final Settlement Respond"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "final_settlement_respond",
            "final_settlement_respond",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, lease_id):
        from core_apps.features.services.settlement_commands import respond_settlement

        result = respond_settlement(
            request.user,
            request.auth,
            request.data,
            request.headers.get("X-Sokoun-Authorization", ""),
            lease_id,
        )
        return Response(result.data, status=result.status)


# Stable callable import for integrations; URLs use the explicit class.
final_settlement_respond = FinalSettlementRespondView.as_view()


from core_apps.features.services.money_projection import (
    refund_payload as refund_payload,
)


def _refund(request, refund_id, allow_operations=False, lock=False):
    from ..services.money_access import refund_for

    return refund_for(request.user, refund_id, allow_operations, lock)


__all__ = [
    "FinalSettlementRespondView",
    "_refund",
    "final_settlement_respond",
    "refund_payload",
]
