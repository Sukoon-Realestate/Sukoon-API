from core_apps.features.http import ActionPolicy, FeatureAPIView

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .renderers import FeatureJsonRenderer
from .services import decision_notebooks


class Context(serializers.Serializer):
    workspace = serializers.ChoiceField(
        choices=["individual", "owner", "student", "company"]
    )
    company_id = serializers.UUIDField(required=False)


class Sync(serializers.Serializer):
    operation_id = serializers.UUIDField()
    base_revision = serializers.IntegerField(min_value=0)
    content = serializers.JSONField()


class Resolve(serializers.Serializer):
    operation_id = serializers.UUIDField()
    base_revision = serializers.IntegerField(min_value=0)
    conflict_id = serializers.UUIDField()
    resolution = serializers.ChoiceField(choices=["current", "incoming"])


def context(request):
    value = Context(data=request.query_params)
    value.is_valid(raise_exception=True)
    return value.validated_data["workspace"], str(
        value.validated_data.get("company_id", "")
    )


class NotebookView(FeatureAPIView):
    name = "Notebook"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "decision_views",
            "notebook",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "decision_views",
            "notebook",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        workspace, company = context(request)
        return Response(decision_notebooks.read(request.user, workspace, company))

    def post(self, request):
        workspace, company = context(request)
        body = Sync(data=request.data)
        body.is_valid(raise_exception=True)
        return Response(
            decision_notebooks.write(
                request.user, workspace, company, body.validated_data
            )
        )


# Stable callable import for integrations; URLs use the explicit class.
notebook = NotebookView.as_view()


class ResolveView(FeatureAPIView):
    name = "Resolve"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "decision_views",
            "resolve",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request):
        workspace, company = context(request)
        body = Resolve(data=request.data)
        body.is_valid(raise_exception=True)
        return Response(
            decision_notebooks.write(
                request.user, workspace, company, body.validated_data
            )
        )


# Stable callable import for integrations; URLs use the explicit class.
resolve = ResolveView.as_view()
