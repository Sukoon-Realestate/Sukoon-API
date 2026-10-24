from rest_framework import serializers
from rest_framework.decorators import (
    api_view,
    permission_classes,
    renderer_classes,
    authentication_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .renderers import FeatureJsonRenderer
from .billing_serializers import StoreVerifySerializer
from .services.store_payments import account_context, verify_purchase
from .services.entitlements import decision
from .services.billing_catalog import workspace_for
from .services.commerce_access import organization_for


def platform_for(request):
    return serializers.ChoiceField(choices=["ios", "android"]).run_validation(
        request.query_params.get("platform")
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def store_context(request):
    return Response(account_context(request.user, platform_for(request)))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def store_verify(request):
    serializer = StoreVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(verify_purchase(request.user, serializer.validated_data))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def entitlements(request):
    organization = organization_for(
        request.user, request.query_params.get("organization_id")
    )
    workspace = workspace_for(request.query_params.get("workspace", "tenant"))
    return Response(
        decision(
            request.user,
            request.query_params.get("feature", ""),
            workspace,
            organization,
        )
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
@renderer_classes([FeatureJsonRenderer])
def store_notification(request, platform):
    if platform not in {"ios", "android"}:
        raise serializers.ValidationError({"platform": "Unsupported store."})
    from .services.store_notifications import handle_notification

    return Response(handle_notification(platform, request.body, request.headers))
