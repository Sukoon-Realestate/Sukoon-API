from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SubscriptionPlan
from .renderers import FeatureJsonRenderer
from .services.billing_catalog import (
    current_subscription,
    plan_payload,
    subscription_payload,
    workspace_for,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def plans(request):
    workspace = workspace_for(request.query_params.get("workspace", "tenant"))
    language = (
        "ar" if getattr(request, "LANGUAGE_CODE", "en").startswith("ar") else "en"
    )
    from .services.commerce_access import organization_for

    organization = organization_for(
        request.user, request.query_params.get("organization_id")
    )
    plans = SubscriptionPlan.objects.filter(
        active=True, audience="organization" if organization else "personal"
    ).filter(Q(workspace=workspace) | Q(workspace="both"))
    values = [plan_payload(plan, language, user=request.user) for plan in plans]
    if request.query_params.get("projection") == "mobile_v1" or organization:
        return Response(catalog(request, workspace, organization, values))
    return Response(values)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def current(request):
    workspace = workspace_for(request.query_params.get("workspace", "tenant"))
    from .services.commerce_access import organization_for

    organization = organization_for(
        request.user, request.query_params.get("organization_id")
    )
    if request.query_params.get("projection") == "mobile_v1" or organization:
        language = (
            "ar" if getattr(request, "LANGUAGE_CODE", "en").startswith("ar") else "en"
        )
        values = [
            plan_payload(p, language, user=request.user)
            for p in SubscriptionPlan.objects.filter(
                active=True,
                workspace__in=[workspace, "both"],
                audience="organization" if organization else "personal",
            )
        ]
        return Response(catalog(request, workspace, organization, values))
    return Response(
        {
            "subscription": subscription_payload(
                current_subscription(request.user, workspace)
            ),
            "is_subscriped": True,
            "workspace": workspace,
            "plans": [
                plan_payload(
                    plan,
                    (
                        "ar"
                        if getattr(request, "LANGUAGE_CODE", "en").startswith("ar")
                        else "en"
                    ),
                    user=request.user,
                )
                for plan in SubscriptionPlan.objects.filter(
                    active=True, audience="personal", workspace__in=[workspace, "both"]
                )
            ],
        }
    )


def catalog(request, workspace, organization, plans):
    subscription = current_subscription(request.user, workspace, organization)
    return {
        "contract_version": 1,
        "organization_id": str(organization.id) if organization else "",
        "workspace": workspace,
        "plans": plans,
        "subscription": subscription_payload(subscription),
        "management": {
            "platform": subscription.store_platform if subscription else "",
            "auto_renew": subscription.auto_renew if subscription else False,
            "renews_at": (
                subscription.ends_at.isoformat()
                if subscription and subscription.auto_renew
                else None
            ),
        },
    }
