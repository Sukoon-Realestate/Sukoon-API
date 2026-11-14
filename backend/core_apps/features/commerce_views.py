from core_apps.features.http import ActionPolicy, FeatureAPIView

from rest_framework import serializers
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


class StoreContextView(FeatureAPIView):
    name = "Store Context"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "commerce_views",
            "store_context",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        return Response(account_context(request.user, platform_for(request)))


# Stable callable import for integrations; URLs use the explicit class.
store_context = StoreContextView.as_view()


class StoreVerifyView(FeatureAPIView):
    name = "Store Verify"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "commerce_views",
            "store_verify",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request):
        serializer = StoreVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(verify_purchase(request.user, serializer.validated_data))


# Stable callable import for integrations; URLs use the explicit class.
store_verify = StoreVerifyView.as_view()


class EntitlementsView(FeatureAPIView):
    name = "Entitlements"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "commerce_views",
            "entitlements",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
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


# Stable callable import for integrations; URLs use the explicit class.
entitlements = EntitlementsView.as_view()


class StoreNotificationView(FeatureAPIView):
    name = "Store Notification"
    http_method_names = ["post", "options"]
    authentication_classes = []
    permission_classes = []
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "commerce_views",
            "store_notification",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, platform):
        if platform not in {"ios", "android"}:
            raise serializers.ValidationError({"platform": "Unsupported store."})
        from .services.store_notifications import handle_notification

        return Response(handle_notification(platform, request.body, request.headers))


# Stable callable import for integrations; URLs use the explicit class.
store_notification = StoreNotificationView.as_view()
