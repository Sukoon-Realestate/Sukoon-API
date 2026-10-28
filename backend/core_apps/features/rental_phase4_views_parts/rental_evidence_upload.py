"""Rental phase4 views: rental evidence upload."""

import hashlib
import uuid
from datetime import timedelta
from django.db import transaction
from django.core import signing
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import RentalEvidence
from ..services import evidence_storage
from core_apps.common.private_media_policy import inspect, maximum, MIME_EXTENSIONS
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .handover_payload import (
    PNG_MAGIC,
    MAX_EVIDENCE_BYTES,
    _lease as _personal_lease,
    evidence_payload,
)


def _lease(request, identity, *, lock=False):
    from ..models import Lease
    from django.contrib.auth import get_user_model

    from ..providers import require_verified_rental_account

    users = get_user_model().objects
    if lock:
        users = users.select_for_update()
    actor = get_object_or_404(users, pk=request.user.pk)
    require_verified_rental_account(actor)
    lease = get_object_or_404(Lease, id=identity)
    evidence_storage.require_available()
    if not lease.renter_company_id:
        if lock:
            lease = Lease.objects.select_for_update().get(pk=lease.pk)
        if request.user.pk not in {lease.owner_id, lease.tenant_id}:
            raise NotFound()
        if lease.legacy_read_only:
            raise RentalConflict("Historical evidence requires an explicit review.")
        return lease
    from ..services.company.tenancy_access import get, require_role

    item = get(request.user, lease.company_tenancy.id, lock=lock)
    require_role(item, request.user, {"owner", "coordinator", "payer"})
    return item.lease


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
@parser_classes([MultiPartParser, FormParser])
def rental_evidence_upload(request):
    lease_id = request.data.get("lease_id")
    request_key = request.data.get("request_key")
    upload = request.FILES.get("file")
    claimed_type = request.data.get("mime_type")
    claimed_digest = request.data.get("sha256", "").lower()
    if not all([lease_id, request_key, upload, claimed_type, claimed_digest]):
        raise ValidationError(
            "lease_id, file, mime_type, sha256, and request_key are required."
        )
    try:
        request_key = uuid.UUID(str(request_key))
    except ValueError:
        raise ValidationError({"request_key": "Must be a UUID."})
    operation = f"rental_evidence.upload.{lease_id}"
    lease = _lease(request, lease_id)
    existing = RentalEvidence.objects.filter(
        uploader=request.user, lease__id=lease_id, request_key=request_key
    ).first()
    if existing:
        if existing.sha256 != claimed_digest:
            raise RentalConflict(
                "The request key belongs to different evidence.",
                code="idempotency_conflict",
            )
        record = replay_operation(
            request.user,
            operation,
            request_key,
            {"lease_id": str(lease_id), "sha256": claimed_digest},
        )
        if record:
            return Response(record[0], status=record[1])
    if upload.content_type != claimed_type:
        raise ValidationError({"mime_type": "The declared file types must match."})
    content = upload.read(maximum(claimed_type) + 1)
    metadata = inspect(content, claimed_type, digest=claimed_digest, deep=False)
    digest = metadata["sha256"]
    with transaction.atomic():
        lease = _lease(request, lease_id, lock=True)
        record = replay_operation(
            request.user,
            operation,
            request_key,
            {"lease_id": str(lease_id), "sha256": claimed_digest},
        )
        if record:
            return Response(record[0], status=record[1])
        evidence = RentalEvidence(
            lease=lease,
            uploader=request.user,
            request_key=request_key,
            original_name=upload.name,
            content_type=claimed_type,
            media_metadata=metadata,
            size_bytes=len(content),
            sha256=digest,
            storage_provider="pending",
            private_content=content,
        )
        if lease.renter_company_id:
            from ..services.company.role_context import selected

            role = selected(request.user, lease.renter_company, required=False)
            evidence.media_metadata = {
                **(metadata or {}),
                "company_role": role or "owner",
            }
        evidence.storage_key = f"evidence-pending/{evidence.id}"
        evidence.save()
        resource = evidence_payload(evidence)
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload={"lease_id": str(lease.id), "sha256": digest},
            request_subject_id=lease.id,
            result_subject_id=evidence.id,
            result_revision=evidence.revision,
            resource=resource,
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


def _evidence(request, evidence_id):
    item = get_object_or_404(
        RentalEvidence.objects.select_related("lease__owner", "lease__tenant"),
        id=evidence_id,
        deleted_at__isnull=True,
        purpose="rental",
    )
    from ..services.company.role_evidence import can_read

    if not can_read(item, request.user):
        raise NotFound()
    if not request.user.is_active:
        raise NotFound()
    return item


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_evidence_detail(request, evidence_id):
    return Response(evidence_payload(_evidence(request, evidence_id)))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_evidence_download(request, evidence_id):

    item = _evidence(request, evidence_id)
    if item.malware_status != RentalEvidence.MalwareStatus.SAFE:
        raise RentalConflict("Evidence is not ready for download.")
    expires = timezone.now() + timedelta(minutes=5)
    return Response(
        {
            "id": str(item.id),
            "subject_id": str(item.lease.id),
            "url": request.build_absolute_uri(
                reverse("rental-evidence-content", kwargs={"evidence_id": item.id})
            )
            + "?grant="
            + signing.dumps(
                {
                    "id": str(item.id),
                    "user": str(request.user.pk),
                    "revision": item.revision,
                },
                salt="evidence-read",
            ),
            "requires_auth": True,
            "expires_at": expires.isoformat(),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def rental_evidence_content(request, evidence_id):
    from django.core import signing
    from django.http import HttpResponse

    item = _evidence(request, evidence_id)
    try:
        grant = signing.loads(
            request.query_params.get("grant", ""), salt="evidence-read", max_age=300
        )
    except signing.BadSignature as error:
        raise NotFound() from error
    if (
        grant
        != {"id": str(item.id), "user": str(request.user.pk), "revision": item.revision}
        or item.malware_status != "safe"
    ):
        raise NotFound()
    response = HttpResponse(evidence_storage.read(item), content_type=item.content_type)
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = (
        f'attachment; filename="rental-evidence.{MIME_EXTENSIONS.get(item.content_type, "bin")}"'
    )
    return response
