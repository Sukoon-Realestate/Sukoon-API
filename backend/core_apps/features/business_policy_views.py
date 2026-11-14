from core_apps.features.http import ActionPolicy, FeatureAPIView

from django.shortcuts import get_object_or_404
from django.utils.translation import get_language
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import PolicyDecision
from .renderers import FeatureJsonRenderer
from .services import business_policies as policies


def language():
    return "ar" if (get_language() or "en").startswith("ar") else "en"


class CurrentPoliciesView(FeatureAPIView):
    name = "Current Policies"
    http_method_names = ["get", "options"]
    permission_classes = [AllowAny]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "business_policy_views",
            "current_policies",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        items = [
            policies.public(item, language())
            for code in policies.publication_codes()
            if (item := policies.current(code, publication=True))
        ]
        return Response(
            {
                "items": items,
                "application": "new_actions_only; accepted snapshots remain authoritative",
            }
        )


# Stable callable import for integrations; URLs use the explicit class.
current_policies = CurrentPoliciesView.as_view()


class PolicyVersionView(FeatureAPIView):
    name = "Policy Version"
    http_method_names = ["get", "options"]
    permission_classes = [AllowAny]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "business_policy_views",
            "policy_version",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, code, version):
        policies.publication_definition(code)
        item = get_object_or_404(
            PolicyDecision,
            code=code,
            version=version,
            status__in=["approved", "retired"],
            presentation__contract="public-business-policy-v1",
        )
        return Response(policies.public(item, language()))


# Stable callable import for integrations; URLs use the explicit class.
policy_version = PolicyVersionView.as_view()


class AdministerPoliciesView(FeatureAPIView):
    name = "Administer Policies"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "business_policy_views",
            "administer_policies",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "business_policy_views",
            "administer_policies",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        policies.administrator(request.user)
        return Response({"items": policies.templates()})

    def post(self, request):
        policies.administrator(request.user)
        result, status = policies.publish(request.user, request.data)
        return Response(result, status=status)


# Stable callable import for integrations; URLs use the explicit class.
administer_policies = AdministerPoliciesView.as_view()
