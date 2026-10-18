from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .renderers import FeatureJsonRenderer
from .services.purchase_routing import routing


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def purchase_route(request):
    purpose = request.query_params.get("purpose", "unknown")
    return Response(
        routing(
            purpose,
            request.query_params.get("platform", "unknown"),
            product_id=request.query_params.get("product_id", "")[:100],
        )
    )
