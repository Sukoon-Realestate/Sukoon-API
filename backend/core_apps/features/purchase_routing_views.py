from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .renderers import FeatureJsonRenderer
from .services.purchase_routing import routing_v1


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def purchase_route(request):
    purpose = request.query_params.get("purpose", "unknown")
    from .models import StoreProduct
    from .services.commerce_access import organization_for

    organization = organization_for(
        request.user, request.query_params.get("organization_id")
    )
    platform = request.query_params.get("platform", "unknown")
    product = (
        StoreProduct.objects.filter(
            product_id=request.query_params.get("product_id", ""), platform=platform
        )
        .select_related("plan")
        .first()
    )
    plan = product.plan if product else None
    if plan and (plan.audience == "organization") != bool(organization):
        plan = None
    return Response(
        routing_v1(
            purpose,
            platform,
            plan=plan,
            user=request.user,
            organization=bool(organization),
        )
    )
