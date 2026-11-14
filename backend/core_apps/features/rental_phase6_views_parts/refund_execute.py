"""Rental phase6 views: refund execute."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from ..models import (
    DepositAgreement,
    FinalSettlement,
    Lease,
    MaintenanceRequest,
    RefundRequest,
    RentalChange,
    RentalDispute,
    RentalHandover,
    RentalPayout,
    RentInvoice,
    PrivateAccessRevocation,
)
from ..renderers import FeatureJsonRenderer
from ..services.cycle_permissions import cycle_actions


SUBJECT_MODELS = {
    "invoice": RentInvoice,
    "deposit": DepositAgreement,
    "handover": RentalHandover,
    "maintenance": MaintenanceRequest,
    "change": RentalChange,
    "payout": RentalPayout,
    "refund": RefundRequest,
    "settlement": FinalSettlement,
}


class RefundExecuteView(FeatureAPIView):
    "Operations command; the worker calls the same idempotent service."
    name = "Refund Execute"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "refund_execute",
            "refund_execute",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, refund_id):
        from ..services.refund_commands import execute_refund_command

        result = execute_refund_command(
            request.user,
            request.auth,
            request.data,
            request.headers.get("X-Sokoun-Authorization", ""),
            refund_id,
        )
        return Response(result.data, status=result.status)


# Stable callable import for integrations; URLs use the explicit class.
refund_execute = RefundExecuteView.as_view()


def dispute_payload(item, user=None):
    from ..rental_phase4_views_parts.handover_payload import evidence_payload

    return {
        "allowed_actions": cycle_actions(user, item),
        "blocking_reasons": [],
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "subject_kind": item.subject_kind,
        "subject_id": str(item.subject_id),
        "revision": item.revision,
        "status": item.status,
        "reason": item.reason,
        "resolution": item.resolution,
        "responses": item.responses,
        "evidence": [
            evidence_payload(x) for x in item.evidence.all() if not x.deleted_at
        ],
    }


def _dispute(request, dispute_id, allow_operations=False, lock=False):
    if lock:
        lease_id = get_object_or_404(RentalDispute, id=dispute_id).lease_id
        from ..services.rental_lifecycle.locks import lock_financial_lease

        lock_financial_lease(Lease.objects.get(pk=lease_id))
    queryset = RentalDispute.objects.select_related(
        "lease__owner", "lease__tenant"
    ).prefetch_related("evidence")
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    item = get_object_or_404(queryset, id=dispute_id)
    operator = False
    if allow_operations:
        from core_apps.admin_api.permissions import require_staff_actor

        try:
            require_staff_actor(request.user, {StaffProfile.RoleName.DISPUTE_RESOLVER})
            operator = True
        except PermissionDenied:
            pass
    party = request.user in (item.lease.owner, item.lease.tenant)
    revoked = PrivateAccessRevocation.objects.filter(
        lease=item.lease, user=request.user
    ).exists()
    if (party and revoked) or (not party and not operator):
        raise NotFound()
    return item


__all__ = [
    "RefundExecuteView",
    "SUBJECT_MODELS",
    "_dispute",
    "dispute_payload",
    "refund_execute",
]
