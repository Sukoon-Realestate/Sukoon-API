"""Views: lease configuration."""

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.properties.models import Property
from ..models import TenancyInvitation
from ..pagination import FeaturePagination
from ..renderers import FeatureJsonRenderer
from ..services.tenancy_invitations import (
    invitation_is_eligible,
    localized,
    refresh_effective_status,
)
from .rental_operation_lookup import LEASE_TEMPLATES


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_configuration(request):
    from ..services.rental_phase2 import ensure_policy

    policy = ensure_policy()
    from ..services.negotiation_terms import FIXED_TEMPLATE_TERMS
    # This contract configures template/invitation drafts. Structured agreement
    # creation continues to enforce its own onboarding and provider policy.
    can_create = bool(request.user.is_active and request.user.is_verified)
    return Response(
        {
            "can_create": can_create,
            "templates": LEASE_TEMPLATES,
            "fixed_terms": FIXED_TEMPLATE_TERMS,
            "policy": {
                "version": policy.version,
                "commission_rate_bps": policy.commission_rate_bps,
                "commission_payer": policy.commission_payer,
                "commission_basis": policy.commission_basis,
                "processing_fee_payer": policy.processing_fee_payer,
                "renewal_commission_rate_bps": policy.renewal_commission_rate_bps,
                "timezone": policy.timezone,
                "billing_cycle": policy.billing_cycle,
                "currency": policy.currency,
                "exponent": policy.exponent,
            },
            "allowed_actions": ["create"] if can_create else [],
            "blocking_reasons": (
                []
                if can_create
                else [
                    localized(
                        request,
                        "A verified active owner account is required.",
                        "يلزم حساب مالك نشط وموثّق.",
                    )
                ]
            ),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_tenants(request):
    property_id = request.query_params.get("property_id")
    if not property_id:
        raise ValidationError({"property_id": "This query parameter is required."})
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    if not request.user.is_active or not request.user.is_verified:
        raise PermissionDenied("A verified active owner account is required.")
    queryset = TenancyInvitation.objects.filter(
        property=property_obj,
        owner=request.user,
        status=TenancyInvitation.Status.ACCEPTED,
        lease__isnull=True,
    ).select_related("property", "property__owner", "owner", "tenant", "lease")
    offer_id = request.query_params.get("offer_id")
    if offer_id:
        queryset = queryset.filter(offer_id=offer_id)
    eligible = []
    seen = set()
    for invitation in queryset.order_by("-created_at", "-id"):
        refresh_effective_status(invitation)
        if invitation_is_eligible(invitation) and invitation.tenant_id not in seen:
            seen.add(invitation.tenant_id)
            eligible.append(invitation)
    paginator = FeaturePagination()
    page = paginator.paginate_queryset(eligible, request)
    return paginator.get_paginated_response(
        [
            {
                "id": str(invitation.tenant.id),
                "display_name": invitation.tenant.get_full_name,
            }
            for invitation in page
        ]
    )
