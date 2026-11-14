"""Rental phase6 views: refund requests."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import RefundRequest
from ..renderers import FeatureJsonRenderer
from .final_settlement_respond import refund_payload, _refund


class RefundRequestsView(FeatureAPIView):
    name = "Refund Requests"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "refund_requests",
            "refund_requests",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "refund_requests",
            "refund_requests",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        if request.query_params.get("projection") == "compact_v1":
            from ..financial_http import compact_financial_response

            return compact_financial_response(request, "refunds")
        workspace = request.query_params.get("workspace")
        queryset = (
            RefundRequest.objects.filter(lease__owner=request.user)
            if workspace == "owner"
            else RefundRequest.objects.filter(lease__tenant=request.user)
        )
        if request.query_params.get("lease_id"):
            queryset = queryset.filter(lease__id=request.query_params["lease_id"])
        queryset = queryset.exclude(
            lease__private_access_revocations__user=request.user
        )
        results = [
            refund_payload(x)
            for x in queryset.select_related("lease", "payment_attempt__invoice")
        ]
        return Response(
            {"count": len(results), "next": None, "previous": None, "results": results}
        )

    def post(self, request):
        from ..services.refund_commands import request_refund

        result = request_refund(
            request.user,
            request.auth,
            request.data,
            request.headers.get("X-Sokoun-Authorization", ""),
        )
        return Response(result.data, status=result.status)


# Stable callable import for integrations; URLs use the explicit class.
refund_requests = RefundRequestsView.as_view()


class RefundDetailView(FeatureAPIView):
    name = "Refund Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "refund_requests",
            "refund_detail",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, refund_id):
        return Response(refund_payload(_refund(request, refund_id)))


# Stable callable import for integrations; URLs use the explicit class.
refund_detail = RefundDetailView.as_view()


class RefundRespondView(FeatureAPIView):
    name = "Refund Respond"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "refund_requests",
            "refund_respond",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, refund_id):
        from ..services.refund_commands import respond_refund

        result = respond_refund(
            request.user,
            request.auth,
            request.data,
            request.headers.get("X-Sokoun-Authorization", ""),
            refund_id,
        )
        return Response(result.data, status=result.status)


# Stable callable import for integrations; URLs use the explicit class.
refund_respond = RefundRespondView.as_view()

__all__ = [
    "RefundDetailView",
    "RefundRequestsView",
    "RefundRespondView",
    "refund_detail",
    "refund_requests",
    "refund_respond",
]
