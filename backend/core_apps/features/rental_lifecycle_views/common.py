from functools import wraps
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..renderers import FeatureJsonRenderer
from ..pagination import FeaturePagination
from ..services.rental_lifecycle.common import command


def endpoint(methods):
    def decorate(function):
        return api_view(methods)(
            permission_classes([IsAuthenticated])(
                renderer_classes([FeatureJsonRenderer])(function)
            )
        )

    return decorate


def validated(serializer, data):
    body = serializer(data=data)
    body.is_valid(raise_exception=True)
    return body.validated_data


def mutate(request, operation, authorize, execute, *, account_parties=None):
    payload, status = command(
        user=request.user,
        operation=operation,
        data=request.data,
        authorize=authorize,
        execute=execute,
        account_parties=account_parties,
    )
    return Response(payload, status=status)


def page(request, queryset, mapper):
    paginator = FeaturePagination()
    values = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response([mapper(item) for item in values])
