"""Narrow financial review; reading an original outcome never submits a refund."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from core_apps.users.models import User
from core_apps.users.services import totp
from .models import RefundRequest, PaymobRefund
from .pagination import FeaturePagination
from .renderers import FeatureJsonRenderer
from .services import paymob_client, paymob_refunds
from .services.rental_lifecycle.common import staff_role
from .rental_phase6_views_parts.final_settlement_respond import refund_payload


def reader(user):
    current = User.objects.get(pk=user.pk)
    if not staff_role(current, paymob_refunds.ROLES | {"psp_reconciliation"}):
        raise PermissionDenied("A current refund or reconciliation role is required.")
    return current


from core_apps.features.services.money_projection import details as details


def projection(refund, user):
    item = PaymobRefund.objects.filter(refund=refund, current=True).first()
    can_manage = staff_role(user, paymob_refunds.ROLES)
    restricted = user.sensitive_actions_frozen or totp.pending_recovery(user)
    supported = hasattr(refund.payment_attempt, "paymob_payment")
    can_execute = (
        can_manage and refund.status == "approved" and item is None and supported
    )
    can_reauthorize = (
        can_manage
        and item is not None
        and item.status == "held"
        and item.failure_code == "authorization_changed"
        and item.submitted_at is None
    )
    can_retry = (
        can_manage
        and refund.status == "failed"
        and refund.failure_code == "provider_declined"
        and item is not None
        and item.status == "failed"
        and item.resolved_at is not None
        and item.result_snapshot.get("success") is False
        and item.result_snapshot.get("pending") is False
    )
    actions = []
    reasons = []
    if item and item.status in {
        "submitting",
        "processing",
        "unknown",
        "confirmed",
        "failed",
    }:
        actions.append("reconcile")
    if restricted:
        reasons.append(
            "راجع أمان الحساب قبل إجراء حساس جديد؛ متابعة النتيجة السابقة متاحة."
        )
    elif not paymob_client.refund_ready():
        reasons.append("يحتاج إرسال الاسترداد إلى تجهيز حساب الاختبار الحالي.")
    else:
        if can_execute:
            actions.append("execute")
        if can_reauthorize:
            actions.append("reauthorize")
        if can_retry:
            actions.append("retry")
    if can_manage and refund.status == "requested" and not restricted:
        actions.extend(["approve", "reject"])
    return {
        "resource": refund_payload(refund),
        "instruction_status": item.status if item else None,
        "instruction_id": str(item.id) if item else None,
        "provider_reference": item.provider_transaction_id if item else None,
        "submitted_at": (
            item.submitted_at.isoformat() if item and item.submitted_at else None
        ),
        "can_execute": can_execute,
        "can_reauthorize": can_reauthorize,
        "can_retry": can_retry,
        "allowed_actions": actions,
        "blocking_reasons": reasons,
        "authorization_details": details(refund),
    }


def private(data):
    response = Response(data)
    response["Cache-Control"] = "private, no-store"
    return response


class QueueView(FeatureAPIView):
    name = "Queue"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "refund_operations",
            "queue",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        current = reader(request.user)
        paginator = FeaturePagination()
        rows = RefundRequest.objects.select_related(
            "lease", "payment_attempt__invoice"
        ).order_by("-created_at", "-pk")
        page = paginator.paginate_queryset(rows, request)
        response = paginator.get_paginated_response(
            [projection(row, current) for row in page]
        )
        response["Cache-Control"] = "private, no-store"
        return response


# Stable callable import for integrations; URLs use the explicit class.
queue = QueueView.as_view()


class ReviewView(FeatureAPIView):
    name = "Review"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "refund_operations",
            "review",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, refund_id):
        current = reader(request.user)
        refund = get_object_or_404(
            RefundRequest.objects.select_related("lease", "payment_attempt__invoice"),
            id=refund_id,
        )
        return private(projection(refund, current))


# Stable callable import for integrations; URLs use the explicit class.
review = ReviewView.as_view()


class ReconcileView(FeatureAPIView):
    name = "Reconcile"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "refund_operations",
            "reconcile",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, refund_id):
        reader(request.user)
        item = get_object_or_404(PaymobRefund, refund__id=refund_id, current=True)
        if request.data.get("provider_transaction_id"):
            paymob_refunds.verify_result(
                item, candidate_id=request.data["provider_transaction_id"]
            )
        else:
            paymob_refunds.process(item, allow_submit=False)
        current = reader(request.user)
        return private(
            projection(RefundRequest.objects.get(pk=item.refund_id), current)
        )


# Stable callable import for integrations; URLs use the explicit class.
reconcile = ReconcileView.as_view()


class RetryView(FeatureAPIView):
    name = "Retry"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "refund_operations",
            "retry",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, refund_id):
        from core_apps.features.services.refund_commands import retry_refund

        result = retry_refund(
            request.user,
            request.auth,
            request.data,
            request.headers.get("X-Sokoun-Authorization", ""),
            refund_id,
        )
        return Response(result.data, status=result.status)


# Stable callable import for integrations; URLs use the explicit class.
retry = RetryView.as_view()


class ReauthorizeView(FeatureAPIView):
    name = "Reauthorize"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "refund_operations",
            "reauthorize",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, refund_id):
        from core_apps.features.services.refund_commands import reauthorize_refund

        result = reauthorize_refund(
            request.user,
            request.auth,
            request.data,
            request.headers.get("X-Sokoun-Authorization", ""),
            refund_id,
        )
        return Response(result.data, status=result.status)


# Stable callable import for integrations; URLs use the explicit class.
reauthorize = ReauthorizeView.as_view()

__all__ = ["details"]
