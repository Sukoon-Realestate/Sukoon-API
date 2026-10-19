"""Rental phase4 views: rental evidence upload."""

import hashlib
import uuid
from datetime import timedelta
from django.db import transaction
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
from ..providers import get_rental_provider
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

    lease = get_object_or_404(Lease, id=identity)
    if not lease.renter_company_id:
        return _personal_lease(request, identity, lock=lock)
    from ..providers import require_rental_provider
    from ..services.company.tenancy_access import get, require_role

    require_rental_provider(request.user)
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
    lease = _lease(request, lease_id)
    content = upload.read(MAX_EVIDENCE_BYTES + 1)
    if len(content) > MAX_EVIDENCE_BYTES:
        raise ValidationError({"file": "PNG files must be at most 5 MiB."})
    if (
        claimed_type != "image/png"
        or upload.content_type != "image/png"
        or not content.startswith(PNG_MAGIC)
    ):
        raise ValidationError({"file": "Only actual PNG images are accepted."})
    digest = hashlib.sha256(content).hexdigest()
    if digest != claimed_digest:
        raise ValidationError({"sha256": "Digest does not match the uploaded bytes."})
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
            content_type="image/png",
            size_bytes=len(content),
            sha256=digest,
            storage_provider="fake",
            private_content=content,
        )
        evidence.storage_key = get_rental_provider().store_private_evidence(
            lease.id, evidence.id, content
        )
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
    from ..services.company.tenancy_access import commercial_read

    if not commercial_read(item.lease, request.user):
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
            "url": get_rental_provider().create_private_download(item.id, expires),
            "expires_at": expires.isoformat(),
        }
    )
