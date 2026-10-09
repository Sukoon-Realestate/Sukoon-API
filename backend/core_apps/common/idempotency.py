import hashlib
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError

from core_apps.features.models import IdempotencyRecord


class IdempotencyConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Idempotency-Key was reused with different request data."
    default_code = "idempotency_conflict"


def request_key(request):
    """Return a validated optional Idempotency-Key header."""
    value = request.headers.get("Idempotency-Key")
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise ValidationError({"Idempotency-Key": "This header cannot be blank."})
    if len(value) > 100:
        raise ValidationError(
            {"Idempotency-Key": "This header cannot exceed 100 characters."}
        )
    return value


def _file_value(value):
    position = value.tell() if hasattr(value, "tell") else None
    digest = hashlib.sha256()
    try:
        if hasattr(value, "seek"):
            value.seek(0)
        chunks = value.chunks() if hasattr(value, "chunks") else iter(lambda: value.read(65536), b"")
        for chunk in chunks:
            digest.update(chunk)
    finally:
        if position is not None and hasattr(value, "seek"):
            value.seek(position)
    return {
        "name": getattr(value, "name", ""),
        "content_type": getattr(value, "content_type", ""),
        "size": getattr(value, "size", None),
        "sha256": digest.hexdigest(),
    }


def _normalize(value):
    if hasattr(value, "read") and (hasattr(value, "chunks") or hasattr(value, "name")):
        return {"__file__": _file_value(value)}
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, (UUID, Decimal, date, datetime)):
        return str(value)
    if hasattr(value, "pk"):
        return str(value.pk)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def fingerprint(payload):
    encoded = json.dumps(
        _normalize(payload), sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _active_record(*, user, operation, key):
    retention_days = getattr(settings, "IDEMPOTENCY_RETENTION_DAYS", 30)
    cutoff = timezone.now() - timedelta(days=retention_days)
    records = IdempotencyRecord.objects.filter(
        user=user, operation=operation, request_key=key
    )
    record = records.first()
    if record and record.created_at < cutoff:
        records.delete()
        return None
    return record


def _replay(record, expected_fingerprint):
    if record.fingerprint != expected_fingerprint:
        raise IdempotencyConflict()
    if record.recovery_status == IdempotencyRecord.RecoveryStatus.PENDING:
        raise IdempotencyConflict("An operation with this key is still in progress.")
    return record.response_data, record.response_status, True


def execute_idempotent(
    *,
    user,
    operation,
    key,
    payload,
    action,
    request_subject_id=None,
):
    """Execute ``action`` once and atomically persist its response.

    ``action`` returns ``(response_data, response_status, result_subject_id)``.
    The returned tuple adds a final boolean indicating whether the response was replayed.
    """
    if not key:
        data, response_status, result_subject_id = action()
        return data, response_status, False

    expected_fingerprint = fingerprint(payload)
    record = _active_record(user=user, operation=operation, key=key)
    if record:
        return _replay(record, expected_fingerprint)

    try:
        with transaction.atomic():
            record = _active_record(user=user, operation=operation, key=key)
            if record:
                return _replay(record, expected_fingerprint)
            data, response_status, result_subject_id = action()
            IdempotencyRecord.objects.create(
                user=user,
                operation=operation,
                request_key=key,
                fingerprint=expected_fingerprint,
                response_data=data,
                response_status=response_status,
                request_subject_id=request_subject_id,
                result_subject_id=result_subject_id,
                recovery_status=IdempotencyRecord.RecoveryStatus.CONFIRMED,
            )
            return data, response_status, False
    except IntegrityError:
        # A concurrent request may have committed the same key first. Only treat the
        # error as an idempotency race when the corresponding record now exists.
        record = _active_record(user=user, operation=operation, key=key)
        if not record:
            raise
        return _replay(record, expected_fingerprint)


def response_headers(replayed):
    return {"Idempotency-Replayed": "true"} if replayed else {}
