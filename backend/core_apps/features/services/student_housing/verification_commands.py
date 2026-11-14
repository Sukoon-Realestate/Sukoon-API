"""Student Verification command steps; typed adapters retain the HTTP boundary."""

from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.features.models import (
    RentalEvidence,
    RentalVerificationClaim,
    RentalOperationalCase,
)
from core_apps.features.services.rental_lifecycle.common import audit


def student_review_post_apply(profile, revision, *, actor, data):
    evidence = get_object_or_404(
        RentalEvidence,
        id=data["evidence_id"],
        uploader=profile.user,
        purpose="student",
        malware_status="safe",
        deleted_at__isnull=True,
    )
    if not timezone.now() < data["expires_at"] <= timezone.now() + timedelta(days=400):
        raise ValidationError({"expires_at": "A review must expire within 400 days."})
    claim = RentalVerificationClaim.objects.create(
        subject_kind="student_enrollment",
        subject_user=profile.user,
        student_evidence=evidence,
        campus=profile.campus,
        claim_code=data["claim_code"],
        public_wording="Student status reviewed",
        reviewer=actor,
        evidence_reference=str(evidence.id),
        checked_at=timezone.now(),
        expires_at=data["expires_at"],
    )
    profile.revision += 1
    profile.save(update_fields=["revision", "updated_at"])
    audit(claim, actor, "student_verification.reviewed", data["note"])
    for case in RentalOperationalCase.objects.select_for_update().filter(
        source_key=f"student-evidence:{evidence.id}", kind="student_verification"
    ):
        case.assigned_to = actor
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
            actor,
            "case.resolved",
            data["note"],
            metadata={"claim_id": str(claim.id)},
        )
    return profile
