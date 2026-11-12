from .http import IdentityAPIView as APIView
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.common.idempotency import response_headers
from core_apps.features.pagination import FeaturePagination
from . import selectors
from .services import account_closure
from .services.closure_reads import prepare_projections
from .read_pages import history_page


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


class AccountClosureAPIView(APIView):
    name = "Current"  # Preserve OPTIONS metadata.
    http_method_names = ['get', 'post', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request):
        return response(account_closure.summary(request.user, history=history_page(request.query_params)))

    def post(self, request):
        body = RequestBody(data=request.data)
        body.is_valid(raise_exception=True)
        return command(account_closure.submit(request, body.validated_data))


class AccountClosureWithdrawAPIView(APIView):
    name = "Withdraw"  # Preserve OPTIONS metadata.
    http_method_names = ['post', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request, identity):
        body = WithdrawBody(data=request.data)
        body.is_valid(raise_exception=True)
        return command(account_closure.withdraw(request, identity, body.validated_data))


class AccountClosureQueueAPIView(APIView):
    name = "Queue"  # Preserve OPTIONS metadata.
    http_method_names = ['get', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request):
        rows = selectors.closure_queue(request)
        paginator = FeaturePagination()
        page = paginator.paginate_queryset(rows, request)
        page = prepare_projections(page, page=history_page(request.query_params))
        result = paginator.get_paginated_response(
            [account_closure.projection(item, review=True) for item in page]
        )
        result["Cache-Control"] = "private, no-store"
        return result


class AccountClosureReviewAPIView(APIView):
    name = "Review"  # Preserve OPTIONS metadata.
    http_method_names = ['get', 'post', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request, identity):
        return response(selectors.closure_review(request, identity))

    def post(self, request, identity):
        account_closure.require_reviewer(request)
        body = DecisionBody(data=request.data)
        body.is_valid(raise_exception=True)
        return command(account_closure.decide(request, identity, body.validated_data))


class AccountClosureReceiptAPIView(APIView):
    name = "Receipt"  # Preserve OPTIONS metadata.
    http_method_names = ['post', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request):
        operation = serializers.CharField(max_length=120).run_validation(
            request.data.get("operation")
        )
        return response(account_closure.resolve_receipt(request, operation))
