"""Original operation identities and replay receipts, independent of rendering."""

import hashlib
import json
from rest_framework import status
from rest_framework.exceptions import APIException
from ..models import IdempotencyRecord
from .money_result import MoneyResult


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
    return MoneyResult(record.response_data, status=record.response_status)


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
    is_rental_operation=False
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


__all__ = ["Conflict", "_fingerprint", "_remember", "_replay"]
