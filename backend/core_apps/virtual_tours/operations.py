from datetime import timedelta
import re
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from .errors import require
from .models import TourOperation
from .policy import digest


def mutate(request, action, resource, execute):
    """Serialize per account so concurrent retries cannot execute twice.

    All effects are transactional or immutable files; jobs dispatch on commit.
    Receipts have a 30-day life and permanent deduplication tombstones.
    """
    key = request.headers.get("Idempotency-Key", "")
    require(
        bool(re.fullmatch(r"[A-Za-z0-9_-]{8,100}", key)),
        "idempotency_key_required",
        "A stable Idempotency-Key is required.",
        400,
    )
    request_hash = digest(
        {
            "action": action,
            "resource": str(resource),
            "body": request.data,
            "if_match": request.headers.get("If-Match", ""),
        }
    )
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        previous = TourOperation.objects.filter(user=request.user, key=key).first()
        if previous:
            require(
                previous.request_hash == request_hash,
                "idempotency_conflict",
                "This key belongs to a different request.",
                409,
            )
            require(
                previous.expires_at > timezone.now(),
                "operation_expired",
                "Receipt expired. Reconcile the resource; do not repeat the write.",
                410,
            )
            return (
                {**previous.result, "operation_id": str(previous.id)},
                previous.http_status,
                True,
            )
        operation = TourOperation.objects.create(
            user=request.user,
            key=key,
            action=action,
            resource=str(resource),
            request_hash=request_hash,
            expires_at=timezone.now() + timedelta(days=30),
        )
        result, status = execute()
        operation.result, operation.http_status, operation.status = (
            result,
            status,
            "succeeded",
        )
        operation.save(update_fields=["result", "http_status", "status"])
        return {**result, "operation_id": str(operation.id)}, status, False
