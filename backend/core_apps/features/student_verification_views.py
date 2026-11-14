from functools import partial
from .services.student_housing import verification_commands as entry_commands

"""Private enrollment evidence via the existing RentalEvidence/provider workflow."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


import uuid
from datetime import timedelta
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers as s
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from core_apps.users.models import User
from .models import RentalEvidence, StudentProfile
from .services import evidence_storage
from core_apps.common.private_media_policy import inspect, maximum, MIME_EXTENSIONS
from .renderers import FeatureJsonRenderer
from .services.planning import require_planning, mutate, page
from .services.rental_phase2 import RentalConflict, replay_operation, remember_mutation
from .services.rental_lifecycle.common import require_staff, staff_role
from .rental_lifecycle_serializers import CommandBody
from .rental_lifecycle_views.common import validated
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


class StudentEvidenceUploadView(FeatureAPIView):
    name = "Student Evidence Upload"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    parser_classes = [MultiPartParser, FormParser]
    action_policies = {
        "post": ActionPolicy(
            "student_verification_views",
            "student_evidence_upload",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request):
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
            replay = replay_operation(
                request.user, "student_evidence.upload", key, payload
            )
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
                "student_profile_id": str(
                    StudentProfile.objects.get(user=request.user).id
                ),
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


# Stable callable import for integrations; URLs use the explicit class.
student_evidence_upload = StudentEvidenceUploadView.as_view()


class StudentEvidenceMetadataView(FeatureAPIView):
    name = "Student Evidence Metadata"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "student_verification_views",
            "student_evidence_metadata",
            boundary="planning",
            capability="student_verification",
            typed=False,
        ),
    }

    def get(self, request, evidence_id):
        item = get_object_or_404(
            RentalEvidence,
            id=evidence_id,
            purpose="student",
            uploader=request.user,
            deleted_at__isnull=True,
        )
        return Response(evidence_payload(item))


# Stable callable import for integrations; URLs use the explicit class.
student_evidence_metadata = StudentEvidenceMetadataView.as_view()


class StudentEvidenceView(FeatureAPIView):
    name = "Student Evidence"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "student_verification_views",
            "student_evidence",
            boundary="planning",
            capability="student_verification",
            typed=False,
        ),
    }

    def get(self, request, evidence_id=None):
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
                "Evidence is awaiting its private security scan.",
                code="evidence_not_ready",
            )
        require_planning(request.user, "student_verification")
        response = HttpResponse(
            evidence_storage.read(item), content_type=item.content_type
        )
        response["Content-Disposition"] = (
            f'attachment; filename="student-evidence.{MIME_EXTENSIONS.get(item.content_type, "bin")}"'
        )
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response


# Stable callable import for integrations; URLs use the explicit class.
student_evidence = StudentEvidenceView.as_view()


class StudentReviewView(FeatureAPIView):
    name = "Student Review"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "student_verification_views",
            "student_review",
            boundary="planning",
            capability="student_verification",
            typed=False,
        ),
        "post": ActionPolicy(
            "student_verification_views",
            "student_review",
            boundary="planning",
            capability="student_verification",
            typed=False,
        ),
    }

    def get(self, request, profile_id=None):
        require_staff(request.user, {"kyc_reviewer"})
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

    def post(self, request, profile_id=None):
        require_staff(request.user, {"kyc_reviewer"})
        data = validated(StudentReviewBody, request.data)
        apply = partial(
            entry_commands.student_review_post_apply, actor=request.user, data=data
        )
        return mutate(
            request,
            f"student_verification.review.{profile_id}",
            lambda: get_object_or_404(
                StudentProfile.objects.select_for_update(), id=profile_id
            ),
            apply,
            lambda item: profile_payload(item, item.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
student_review = StudentReviewView.as_view()
