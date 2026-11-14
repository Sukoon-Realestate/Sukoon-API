"""Bounded private Home summaries. Every destination still loads fresh permissions."""

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer


from rest_framework.response import Response


class PlanningHomeView(FeatureAPIView):
    name = "Planning Home"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "planning_home_views",
            "planning_home",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        from .services.planning_home import home_summary

        return Response(
            home_summary(request.user, request.query_params.get("workspace", "tenant"))
        )


# Stable callable import for integrations; URLs use the explicit class.
planning_home = PlanningHomeView.as_view()
