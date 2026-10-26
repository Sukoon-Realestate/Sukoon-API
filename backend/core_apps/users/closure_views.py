from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.common.idempotency import response_headers, resolve_or_close, request_key
from core_apps.features.pagination import FeaturePagination
from .models import AccountClosureRequest
from .services import account_closure


class RequestBody(serializers.Serializer):
    expected_revision = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=1000, allow_blank=True, default="")


class WithdrawBody(serializers.Serializer):
    expected_revision = serializers.IntegerField(min_value=1)


class DecisionBody(WithdrawBody):
    decision = serializers.ChoiceField(choices=["wait", "reject", "complete"])
    reason = serializers.CharField(max_length=2000)


def response(value, code=200, headers=None):
    return Response(
        value,
        status=code,
        headers={"Cache-Control": "private, no-store", **(headers or {})},
    )


def command(result):
    data, code, replay = result
    return response(data, code, response_headers(replay))


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def current(request):
    if request.method == "GET":
        return response(account_closure.summary(request.user))
    body = RequestBody(data=request.data)
    body.is_valid(raise_exception=True)
    return command(account_closure.submit(request, body.validated_data))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def withdraw(request, identity):
    body = WithdrawBody(data=request.data)
    body.is_valid(raise_exception=True)
    return command(account_closure.withdraw(request, identity, body.validated_data))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def queue(request):
    account_closure.require_reviewer(request)
    rows = AccountClosureRequest.objects.select_related("user").order_by("created_at")
    if request.query_params.get("history") != "true":
        rows = rows.filter(active=True)
    paginator = FeaturePagination()
    page = paginator.paginate_queryset(rows, request)
    result = paginator.get_paginated_response(
        [account_closure.projection(item, review=True) for item in page]
    )
    result["Cache-Control"] = "private, no-store"
    return result


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def review(request, identity):
    account_closure.require_reviewer(request)
    if request.method == "GET":
        from django.shortcuts import get_object_or_404

        item = get_object_or_404(
            AccountClosureRequest.objects.select_related("user"), id=identity
        )
        return response(account_closure.projection(item, review=True))
    body = DecisionBody(data=request.data)
    body.is_valid(raise_exception=True)
    return command(account_closure.decide(request, identity, body.validated_data))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def receipt(request):
    # Fence a lost command before permitting another; no business operation is replayed.
    operation = serializers.CharField(max_length=120).run_validation(
        request.data.get("operation")
    )
    if not operation.startswith("account.closure."):
        raise serializers.ValidationError("Unsupported account operation.")
    if operation.startswith("account.closure.review:"):
        account_closure.require_reviewer(request)
    record = resolve_or_close(
        user=request.user,
        operation=operation,
        key=request_key(request),
        auth_claims=request.auth or {},
    )
    return response(
        {
            "state": record.recovery_status,
            "response": record.response_data,
            "status_code": record.response_status,
        }
    )
