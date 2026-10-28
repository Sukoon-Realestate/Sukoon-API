"""Views: rental operation lookup."""

import hashlib
import json
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import APIException, ValidationError, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import IdempotencyRecord
from ..pagination import FeaturePagination
from ..renderers import FeatureJsonRenderer
from ..services.rental_foundation import (
    capabilities_for,
    get_authorized_rental_subject,
    private_no_store,
)


User = get_user_model()


FEATURE_DECORATORS = [api_view]


LEASE_TEMPLATES = [
    {
        "id": "eg-residential-v1",
        "title": "Residential lease",
        "jurisdiction": "EG",
        "language": "ar",
        "version": "1",
    }
]


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with current server state."


def _fingerprint(data):
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()


def _replay(user, operation, request_key, payload):
    record = IdempotencyRecord.objects.filter(
        user=user, operation=operation, request_key=request_key
    ).first()
    if not record:
        return None
    if record.recovery_status == IdempotencyRecord.RecoveryStatus.ABSENT_FINAL:
        raise Conflict(
            "This operation was closed without execution. Review the current resource before using a new request key.",
            code="operation_closed",
        )
    if record.fingerprint != _fingerprint(payload):
        raise Conflict(
            "This request_key was already used with a different payload.",
            code="idempotency_conflict",
        )
    return Response(record.response_data, status=record.response_status)


def _remember(
    user,
    operation,
    request_key,
    payload,
    data,
    response_status,
    *,
    request_subject_id=None,
    result_subject_id=None,
    result_revision=None,
    is_rental_operation=False,
):
    return IdempotencyRecord.objects.create(
        user=user,
        operation=operation,
        request_key=request_key,
        fingerprint=_fingerprint(payload),
        response_data=data,
        response_status=response_status,
        request_subject_id=request_subject_id,
        result_subject_id=result_subject_id,
        result_revision=result_revision,
        is_rental_operation=is_rental_operation,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_capabilities(request):
    subject_id = request.query_params.get("subject_id")
    if not subject_id:
        raise ValidationError({"subject_id": "This query parameter is required."})
    subject = get_authorized_rental_subject(request.user, subject_id)
    response = Response(
        capabilities_for(
            request.user,
            subject,
            request.query_params.get("action", ""),
        )
    )
    return private_no_store(response)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_operation_lookup(request, request_key):
    subject_id = request.query_params.get("subject_id")
    if not subject_id:
        raise ValidationError({"subject_id": "This query parameter is required."})
    operation = IdempotencyRecord.objects.filter(
        user=request.user,
        request_key=str(request_key),
        request_subject_id=subject_id,
        is_rental_operation=True,
    ).first()
    departure_receipt = bool(
        operation
        and operation.operation == f"group.leave.{subject_id}"
        and str(operation.result_subject_id) == str(subject_id)
    )
    from ..services.company.responsibility_management import recovery_subject

    administrative_subject = recovery_subject(request.user, subject_id, operation)
    if not departure_receipt and administrative_subject is None:
        get_authorized_rental_subject(request.user, subject_id)
    if operation:
        if administrative_subject is not None:
            if str(operation.result_subject_id) != str(administrative_subject.id):
                raise NotFound()
        elif not departure_receipt:
            get_authorized_rental_subject(request.user, operation.result_subject_id)
        receipt = {
            "id": str(operation.id),
            "subject_id": str(operation.result_subject_id),
            "request_key": operation.request_key,
            "revision": operation.result_revision,
            "status": operation.recovery_status,
        }
        lookup_status = operation.recovery_status
    else:
        # Database absence alone is not a permanent tombstone.
        receipt = None
        lookup_status = IdempotencyRecord.RecoveryStatus.UNKNOWN
    response = Response(
        {
            "request_key": str(request_key),
            "request_subject_id": str(subject_id),
            "status": lookup_status,
            "operation_receipt": receipt,
        }
    )
    return private_no_store(response)


def _paginate(request, queryset, serializer_class):
    paginator = FeaturePagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)
