"""Rental phase4 views: operations execute payout."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import RentalPayout
from ..renderers import FeatureJsonRenderer
from .handover_respond import payout_payload


class PayoutsView(FeatureAPIView):
    name = "Payouts"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "operations_execute_payout",
            "payouts",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        if request.query_params.get("projection") == "compact_v1":
            from ..financial_http import compact_financial_response

            return compact_financial_response(request, "payouts")
        if request.query_params.get("workspace") != "owner":
            raise ValidationError({"workspace": "Must be owner."})
        queryset = RentalPayout.objects.filter(owner=request.user).prefetch_related(
            "payables"
        )
        if request.query_params.get("lease_id"):
            queryset = queryset.filter(lease__id=request.query_params["lease_id"])
        results = [payout_payload(x) for x in queryset]
        return Response(
            {"count": len(results), "next": None, "previous": None, "results": results}
        )


# Stable callable import for integrations; URLs use the explicit class.
payouts = PayoutsView.as_view()


class PayoutDetailView(FeatureAPIView):
    name = "Payout Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "operations_execute_payout",
            "payout_detail",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, payout_id):
        item = get_object_or_404(
            RentalPayout.objects.prefetch_related("payables"),
            id=payout_id,
            owner=request.user,
        )
        return Response(payout_payload(item))


# Stable callable import for integrations; URLs use the explicit class.
payout_detail = PayoutDetailView.as_view()


from ..services.payout_authority import _require_payout_role as _require_payout_role


class OperationsExecutePayoutView(FeatureAPIView):
    name = "Operations Execute Payout"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "operations_execute_payout",
            "operations_execute_payout",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request):
        from ..services.payout_commands import approve_payout

        result = approve_payout(
            request.user,
            request.auth,
            request.data,
            request.headers.get("X-Sokoun-Authorization", ""),
        )
        return Response(result.data, status=result.status)


# Stable callable import for integrations; URLs use the explicit class.
operations_execute_payout = OperationsExecutePayoutView.as_view()

__all__ = [
    "OperationsExecutePayoutView",
    "PayoutDetailView",
    "PayoutsView",
    "_require_payout_role",
    "operations_execute_payout",
    "payout_detail",
    "payouts",
]
