"""Rental phase6 views: final settlement propose."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import FinalSettlement, Lease, PrivateAccessRevocation
from ..providers import require_rental_provider, require_verified_rental_account
from ..renderers import FeatureJsonRenderer


def _money(value):
    return {"amount_minor": value, "currency": "EGP", "exponent": 2}


def _lease(request, lease_id, lock=False, *, provider_required=False):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        (
            require_rental_provider
            if provider_required
            else require_verified_rental_account
        )(request.user)
    queryset = Lease.objects.select_related("owner", "tenant", "property")
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    lease = get_object_or_404(queryset, id=lease_id)
    from ..services.rental_lifecycle.locks import require_personal_workflow

    require_personal_workflow(lease)
    if request.user not in (lease.owner, lease.tenant):
        raise NotFound()
    if PrivateAccessRevocation.objects.filter(lease=lease, user=request.user).exists():
        raise NotFound()
    return lease


from ..services.settlement_projection import settlement_payload as settlement_payload


def _settlement(lease):
    item, _ = FinalSettlement.objects.get_or_create(lease=lease)
    return item


class FinalSettlementDetailView(FeatureAPIView):
    name = "Final Settlement Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "final_settlement_propose",
            "final_settlement_detail",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, lease_id):
        lease = _lease(request, lease_id)
        item = FinalSettlement.objects.filter(lease=lease).first()
        if item is None:
            # An absent draft is a virtual initial state. Only propose persists it.
            item = FinalSettlement(lease=lease)
            item.id = None
        return Response(settlement_payload(item, request.user))


# Stable callable import for integrations; URLs use the explicit class.
final_settlement_detail = FinalSettlementDetailView.as_view()


class FinalSettlementProposeView(FeatureAPIView):
    name = "Final Settlement Propose"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "final_settlement_propose",
            "final_settlement_propose",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, lease_id):
        from core_apps.features.services.settlement_commands import propose_settlement

        result = propose_settlement(
            request.user,
            request.auth,
            request.data,
            request.headers.get("X-Sokoun-Authorization", ""),
            lease_id,
        )
        return Response(result.data, status=result.status)


# Stable callable import for integrations; URLs use the explicit class.
final_settlement_propose = FinalSettlementProposeView.as_view()

__all__ = [
    "FinalSettlementDetailView",
    "FinalSettlementProposeView",
    "_lease",
    "_money",
    "_settlement",
    "final_settlement_detail",
    "final_settlement_propose",
    "settlement_payload",
]
