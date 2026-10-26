"""A webhook queues inquiry; it cannot assert a signature or activate a lease."""

from uuid import UUID
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from core_apps.common.idempotency import (
    execute_idempotent,
    request_key,
    response_headers,
)
from .models import RentalSigningDocument, RentalSigningHint
from .services import signwell_client
from .services.rental_phase2 import RentalConflict
from .services.signing_documents import document_projection
from .rental_phase6_views_parts.lease_reviews import document_lease


class SigningHookThrottle(UserRateThrottle):
    rate = "30/min"


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([SigningHookThrottle])
def signing_callback(request):
    if not signwell_client.ready():
        raise NotFound()
    if not signwell_client.verify_event(request.data):
        raise PermissionDenied("Invalid signing event authentication.")
    try:
        obj = request.data["data"]["object"]
        identity = UUID(str(obj["metadata"]["sokoun_document_id"]))
        provider_id = UUID(str(obj["id"]))
    except (KeyError, TypeError, ValueError):
        raise ValidationError("Use the original provider document event.")
    with transaction.atomic():
        row = (
            RentalSigningDocument.objects.select_for_update()
            .filter(id=identity)
            .first()
        )
        if row and not row.applied_at:
            if (
                row.provider_document_id is None
                and row.hints.filter(checked_at__isnull=True).count() < 20
            ):
                RentalSigningHint.objects.get_or_create(
                    document=row, provider_document_id=provider_id
                )
            row.next_check_at = timezone.now()
            row.save(update_fields=["next_check_at", "updated_at"])
    return Response({"queued": True}, status=202)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def signing_status(request, document_id):
    row = RentalSigningDocument.objects.filter(id=document_id).first()
    if row is None:
        raise NotFound()
    document_lease(request, row.lease.id, provider_required=False)
    if request.method == "GET":
        return Response(
            document_projection(row, request.user),
            headers={"Cache-Control": "private, no-store"},
        )
    if not isinstance(request.data, dict) or set(request.data) != {
        "expected_status",
        "source_hash",
    }:
        raise ValidationError(
            "Supply the status and hash of the reviewed original document."
        )
    key = request_key(request)
    if not key:
        raise ValidationError(
            "Retain an operation key before requesting reconciliation."
        )
    try:
        key = str(UUID(str(key)))
    except ValueError:
        raise ValidationError("Use a UUID operation key.")

    def refresh():
        document_lease(request, row.lease.id, provider_required=False)
        if not signwell_client.ready() and not row.completed_content:
            raise RentalConflict(
                "The signing provider is unavailable.", code="provider_unavailable"
            )
        current = RentalSigningDocument.objects.select_for_update().get(pk=row.pk)
        if str(request.user.id) not in {value["id"] for value in current.recipients}:
            raise PermissionDenied("Only a named signatory can request reconciliation.")
        if (
            current.source_hash != request.data["source_hash"]
            or current.status != request.data["expected_status"]
        ):
            raise RentalConflict(
                "Refresh the current signing state.", code="stale_revision"
            )
        if current.status == "failed" and current.provider_document_id is None:
            current.status = "prepared"
        elif current.status == "review_required" and current.completed_content:
            current.status = "completed"
        current.next_check_at = timezone.now()
        current.save(update_fields=["status", "next_check_at", "updated_at"])
        return document_projection(current, request.user), 200, None

    with transaction.atomic():
        result, code, replayed = execute_idempotent(
            user=request.user,
            operation=f"signing.refresh:{row.id}",
            key=key,
            payload=request.data,
            action=refresh,
            auth_claims=request.auth,
        )
    return Response(result, status=code, headers=response_headers(replayed))
