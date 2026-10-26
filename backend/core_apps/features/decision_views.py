from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .renderers import FeatureJsonRenderer
from .services import decision_notebooks


class Context(serializers.Serializer):
    workspace = serializers.ChoiceField(choices=["individual", "owner", "student", "company"])
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
    return value.validated_data["workspace"], str(value.validated_data.get("company_id", ""))


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def notebook(request):
    workspace, company = context(request)
    if request.method == "GET":
        return Response(decision_notebooks.read(request.user, workspace, company))
    body = Sync(data=request.data)
    body.is_valid(raise_exception=True)
    return Response(decision_notebooks.write(request.user, workspace, company, body.validated_data))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def resolve(request):
    workspace, company = context(request)
    body = Resolve(data=request.data)
    body.is_valid(raise_exception=True)
    return Response(decision_notebooks.write(request.user, workspace, company, body.validated_data))
