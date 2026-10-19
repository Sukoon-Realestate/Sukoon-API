from django.shortcuts import get_object_or_404
from django.utils.translation import get_language
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import PolicyDecision
from .renderers import FeatureJsonRenderer
from .services import business_policies as policies
from .services.business_policy_catalog import CATALOG


def language():
    return "ar" if (get_language() or "en").startswith("ar") else "en"


@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes([FeatureJsonRenderer])
def current_policies(request):
    items = [
        policies.public(item, language())
        for code in CATALOG
        if (item := policies.current(code))
    ]
    return Response(
        {
            "items": items,
            "application": "new_actions_only; accepted snapshots remain authoritative",
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes([FeatureJsonRenderer])
def policy_version(request, code, version):
    item = get_object_or_404(
        PolicyDecision,
        code=code,
        version=version,
        status__in=["approved", "retired"],
        presentation__contract="public-business-policy-v1",
    )
    return Response(policies.public(item, language()))


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def administer_policies(request):
    policies.administrator(request.user)
    if request.method == "GET":
        return Response({"items": policies.templates()})
    result, status = policies.publish(request.user, request.data)
    return Response(result, status=status)
