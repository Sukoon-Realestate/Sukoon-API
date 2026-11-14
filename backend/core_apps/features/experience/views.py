from core_apps.features.http import ActionPolicy, FeatureAPIView

from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..renderers import FeatureJsonRenderer
from .access import FEATURES, enabled, require, scope_for, preferences


class CapabilitiesView(FeatureAPIView):
    name = "Capabilities"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "views", "capabilities", boundary="standard", capability=None, typed=False
        ),
    }

    def get(self, request):
        scope = scope_for(request)
        return Response(
            {
                "version": 1,
                "scope": scope,
                "features": [name for name in FEATURES if enabled(name)],
            }
        )


# Stable callable import for integrations; URLs use the explicit class.
capabilities = CapabilitiesView.as_view()


class PersonalPreferencesView(FeatureAPIView):
    name = "Personal Preferences"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "views",
            "personal_preferences",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "views",
            "personal_preferences",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        from .sync import payload

        require("sync")
        scope = scope_for(request)
        with transaction.atomic():
            item = preferences(request.user, scope, lock=True)
            return Response(payload(item))

    def post(self, request):
        from .sync import payload, merge

        require("sync")
        scope = scope_for(request)
        with transaction.atomic():
            item = preferences(request.user, scope, lock=True)
            merge(item, request.data)
            return Response(payload(item))


# Stable callable import for integrations; URLs use the explicit class.
personal_preferences = PersonalPreferencesView.as_view()
