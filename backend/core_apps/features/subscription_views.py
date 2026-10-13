from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import AccountSubscription, SubscriptionPlan
from .renderers import FeatureJsonRenderer
from .services.billing_catalog import current_subscription, plan_payload, subscription_payload, workspace_for


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def plans(request):
    workspace = workspace_for(request.query_params.get("workspace", "tenant"))
    language = "ar" if getattr(request, "LANGUAGE_CODE", "en").startswith("ar") else "en"
    plans = SubscriptionPlan.objects.filter(active=True).filter(Q(workspace=workspace) | Q(workspace="both"))
    return Response([plan_payload(plan, language) for plan in plans])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def current(request):
    workspace = workspace_for(request.query_params.get("workspace", "tenant"))
    return Response({"subscription": subscription_payload(current_subscription(request.user, workspace)),
                     "is_subscriped": True, "workspace": workspace,
                     "plans": [plan_payload(plan, "ar" if getattr(request, "LANGUAGE_CODE", "en").startswith("ar") else "en")
                               for plan in SubscriptionPlan.objects.filter(active=True, workspace__in=[workspace, "both"])]})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def cancel(request, subscription_id):
    with transaction.atomic():
        subscription = AccountSubscription.objects.select_for_update().filter(id=subscription_id, user=request.user).first()
        if subscription is None:
            raise NotFound()
        if subscription.cancelled_at is None:
            subscription.cancelled_at = timezone.now()
            subscription.save(update_fields=["cancelled_at", "updated_at"])
    return Response(subscription_payload(subscription))
