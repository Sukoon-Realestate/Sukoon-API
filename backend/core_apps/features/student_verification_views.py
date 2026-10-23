"""Private enrollment evidence via the existing RentalEvidence/provider workflow."""

import hashlib
import io
import uuid
from datetime import timedelta
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers as s
from rest_framework.decorators import (
    api_view,
    permission_classes,
    renderer_classes,
    parser_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from core_apps.users.models import User
from .models import (
    RentalEvidence,
    RentalVerificationClaim,
    StudentProfile,
    RentalOperationalCase,
)
from .services import evidence_storage
from core_apps.common.private_media_policy import inspect, maximum, MIME_EXTENSIONS
from .renderers import FeatureJsonRenderer
from .services.planning import require_planning, planning_api, mutate, page
from .services.rental_phase2 import RentalConflict, replay_operation, remember_mutation
from .services.rental_lifecycle.common import require_staff, staff_role, audit
from .rental_lifecycle_serializers import CommandBody
from .rental_lifecycle_views.common import validated
from .rental_phase4_views_parts.handover_payload import MAX_EVIDENCE_BYTES, PNG_MAGIC
from .services.student_housing.profiles import profile_payload


class StudentReviewBody(CommandBody):
    evidence_id = s.UUIDField()
    claim_code = s.ChoiceField(choices=["admission", "enrollment"])
    expires_at = s.DateTimeField()
    note = s.CharField(max_length=1000)


def evidence_payload(item):
    return {
        "id": str(item.id),
        "revision": item.revision,
        "purpose": "student",
        "subject_id": str(item.uploader.id),
        "name": item.original_name,
        "status": {"safe": "ready", "unsafe": "unsafe", "pending": "pending"}.get(
            item.malware_status, "failed"
        ),
        "mime_type": item.content_type,
        "size_bytes": item.size_bytes,
        "media_metadata": item.media_metadata or {},
        "sha256": item.sha256,
    }


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
@parser_classes([MultiPartParser, FormParser])
def student_evidence_upload(request):
    require_planning(request.user, "student_verification")
    if not StudentProfile.objects.filter(user=request.user).exists():
        raise RentalConflict(
            "Save your study profile before submitting evidence.",
            code="student_profile_required",
        )
    try:
        key = uuid.UUID(str(request.data.get("request_key")))
    except (ValueError, TypeError):
        raise ValidationError({"request_key": "A stable UUID is required."})
    upload = request.FILES.get("file")
    if not upload:
        raise ValidationError({"file": "Supply enrollment or admission evidence."})
    content = upload.read(maximum(upload.content_type) + 1)
    metadata = inspect(
        content,
        upload.content_type,
        student=True,
        digest=request.data.get("sha256"),
        deep=False,
    )
    digest = metadata["sha256"]
    evidence_storage.require_available()
    # Commit a durable identity before provider I/O. Retry uses the same evidence.
    with transaction.atomic():
        User.objects.select_for_update(no_key=True).get(pk=request.user.pk)
        payload = {"subject_id": str(request.user.id), "sha256": digest}
        replay = replay_operation(request.user, "student_evidence.upload", key, payload)
        if replay:
            return Response(replay[0], status=replay[1])
        item, _ = RentalEvidence.objects.get_or_create(
            uploader=request.user,
            purpose="student",
            request_key=key,
            defaults={
                "original_name": f"student-evidence.{MIME_EXTENSIONS[upload.content_type]}",
                "content_type": upload.content_type,
                "media_metadata": metadata,
                "sha256": digest,
                "size_bytes": len(content),
                "private_content": content,
                "storage_key": f"student-evidence-pending/{request.user.id}/{key}",
                "storage_provider": "pending",
                "retain_until": timezone.localdate() + timedelta(days=400),
            },
        )
        if item.sha256 != digest or item.deleted_at:
            raise RentalConflict(
                "The request key belongs to different or deleted evidence.",
                code="idempotency_conflict",
            )
        from .services.rental_lifecycle.cases import open_system_case

        case = open_system_case(
            kind="student_verification",
            source_key=f"student-evidence:{item.id}",
            actor=request.user,
            evidence=[item],
            reason="Private admission or enrollment evidence submitted.",
            next_action="Wait for the evidence scan, assign a KYC reviewer, and record a scoped enrollment outcome.",
        )
        case.baseline = {
            "student_profile_id": str(StudentProfile.objects.get(user=request.user).id),
            "student_evidence_id": str(item.id),
        }
        case.save(update_fields=["baseline", "updated_at"])
        output = remember_mutation(
            user=request.user,
            operation="student_evidence.upload",
            request_key=key,
            payload=payload,
            request_subject_id=request.user.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=evidence_payload(item),
            response_status=201,
        )
    # Existing evidence worker persists/scans this durable pending upload. A receipt
    # acknowledges receipt of bytes, never enrollment or successful inspection.
    return Response(output, status=201)


@planning_api(["GET"], "student_verification")
def student_evidence_metadata(request, evidence_id):
    item = get_object_or_404(
        RentalEvidence,
        id=evidence_id,
        purpose="student",
        uploader=request.user,
        deleted_at__isnull=True,
    )
    return Response(evidence_payload(item))


@planning_api(["GET"], "student_verification")
def student_evidence(request, evidence_id=None):
    if evidence_id is None:
        return page(
            request,
            RentalEvidence.objects.filter(
                purpose="student", uploader=request.user, deleted_at__isnull=True
            ).order_by("-created_at"),
            evidence_payload,
        )
    item = get_object_or_404(
        RentalEvidence, id=evidence_id, purpose="student", deleted_at__isnull=True
    )
    if item.uploader_id != request.user.pk and not staff_role(
        request.user, {"kyc_reviewer"}
    ):
        raise NotFound()
    if item.malware_status != "safe":
        raise RentalConflict(
            "Evidence is awaiting its private security scan.", code="evidence_not_ready"
        )
    require_planning(request.user, "student_verification")
    response = HttpResponse(evidence_storage.read(item), content_type=item.content_type)
    response["Content-Disposition"] = (
        f'attachment; filename="student-evidence.{MIME_EXTENSIONS.get(item.content_type, "bin")}"'
    )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@planning_api(["GET", "POST"], "student_verification")
def student_review(request, profile_id=None):
    require_staff(request.user, {"kyc_reviewer"})
    if request.method == "GET":
        return page(
            request,
            StudentProfile.objects.order_by("updated_at", "id"),
            lambda item: {
                **profile_payload(item, item.user),
                "evidence": [
                    evidence_payload(e)
                    for e in RentalEvidence.objects.filter(
                        uploader=item.user, purpose="student", deleted_at__isnull=True
                    )
                ],
            },
        )
    data = validated(StudentReviewBody, request.data)

    def apply(profile, revision):
        evidence = get_object_or_404(
            RentalEvidence,
            id=data["evidence_id"],
            uploader=profile.user,
            purpose="student",
            malware_status="safe",
            deleted_at__isnull=True,
        )
        if (
            not timezone.now()
            < data["expires_at"]
            <= timezone.now() + timedelta(days=400)
        ):
            raise ValidationError(
                {"expires_at": "A review must expire within 400 days."}
            )
        claim = RentalVerificationClaim.objects.create(
            subject_kind="student_enrollment",
            subject_user=profile.user,
            student_evidence=evidence,
            campus=profile.campus,
            claim_code=data["claim_code"],
            public_wording="Student status reviewed",
            reviewer=request.user,
            evidence_reference=str(evidence.id),
            checked_at=timezone.now(),
            expires_at=data["expires_at"],
        )
        profile.revision += 1
        profile.save(update_fields=["revision", "updated_at"])
        audit(claim, request.user, "student_verification.reviewed", data["note"])
        for case in RentalOperationalCase.objects.select_for_update().filter(
            source_key=f"student-evidence:{evidence.id}", kind="student_verification"
        ):
            case.assigned_to = request.user
            case.status, case.resolution_code, case.resolution = (
                "resolved",
                "corrected",
                data["note"],
            )
            case.next_action = "Review future eligibility when the student claim expires or the affiliation changes."
            case.revision += 1
            case.save()
            audit(
                case,
                request.user,
                "case.resolved",
                data["note"],
                metadata={"claim_id": str(claim.id)},
            )
        return profile

    return mutate(
        request,
        f"student_verification.review.{profile_id}",
        lambda: get_object_or_404(
            StudentProfile.objects.select_for_update(), id=profile_id
        ),
        apply,
        lambda item: profile_payload(item, item.user),
    )
