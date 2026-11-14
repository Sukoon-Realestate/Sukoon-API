"""Rental phase4 views: operations reconcile payout."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..renderers import FeatureJsonRenderer


class OperationsReconcilePayoutView(FeatureAPIView):
    name = "Operations Reconcile Payout"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "operations_reconcile_payout",
            "operations_reconcile_payout",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, payout_id):
        from ..services.payout_commands import reconcile_payout

        result = reconcile_payout(
            request.user,
            request.auth,
            request.data,
            request.headers.get("X-Sokoun-Authorization", ""),
            payout_id,
        )
        return Response(result.data, status=result.status)


# Stable callable import for integrations; URLs use the explicit class.
operations_reconcile_payout = OperationsReconcilePayoutView.as_view()

__all__ = ["OperationsReconcilePayoutView", "operations_reconcile_payout"]
