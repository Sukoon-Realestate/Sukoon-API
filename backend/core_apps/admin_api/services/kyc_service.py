import logging
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from core_apps.admin_api.models import KYCSubmission, StaffProfile

logger = logging.getLogger(__name__)


def get_kyc_queue_queryset():
    """
    Returns queryset of KYC submissions optimized with related profile and user data.
    """
    return (
        KYCSubmission.objects.select_related("profile", "profile__user", "reviewer")
        .filter(superseded_at__isnull=True)
        .order_by("-created_at")
    )


def get_kyc_metrics():
    """
    Returns statistical metrics for KYC requests processed today and pending.
    """
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    pending_count = KYCSubmission.objects.filter(
        status=KYCSubmission.Status.PENDING, superseded_at__isnull=True
    ).count()
    accepted_today = KYCSubmission.objects.filter(
        status=KYCSubmission.Status.APPROVED, reviewed_at__gte=today_start
    ).count()
    rejected_today = KYCSubmission.objects.filter(
        status=KYCSubmission.Status.REJECTED, reviewed_at__gte=today_start
    ).count()
    reviewed_today = accepted_today + rejected_today

    return {
        "pendingReview": pending_count,
        "acceptedToday": accepted_today,
        "rejectedToday": rejected_today,
        "reviewedToday": reviewed_today,
    }


def get_kyc_detail(submission_id):
    """
    Returns detail data for a single KYC submission including document images and user verification history.
    """
    try:
        submission = KYCSubmission.objects.select_related(
            "profile", "profile__user", "reviewer"
        ).get(id=submission_id)
    except (KYCSubmission.DoesNotExist, ValueError):
        raise NotFound(f"KYC Submission with ID {submission_id} was not found.")

    user = submission.profile.user
    profile = submission.profile
    evidence = submission.evidence_snapshot
    is_owner = user.properties.exists()

    return {
        "id": str(submission.id),
        "user_id": str(user.id),
        "userName": user.get_full_name or user.email,
        "userEmail": user.email,
        "userPhone": str(profile.phone_number) if profile.phone_number else "غير متوفر",
        "userType": "مالك" if is_owner else "مستأجر",
        "nationalId": evidence.get("national_id", ""),
        "birthDate": evidence.get("birth_date", ""),
        "gender": evidence.get("gender", ""),
        "idFaceUrl": evidence.get("id_face"),
        "idBackUrl": evidence.get("id_back"),
        "selfieUrl": evidence.get("confirmation_selfi"),
        "evidenceDigest": submission.evidence_digest,
        "canReview": bool(
            submission.evidence_digest
            and not submission.superseded_at
            and submission.status == "pending"
        ),
        "status": submission.status,
        "statusDisplay": submission.get_status_display(),
        "submittedAt": submission.created_at.strftime("%Y/%m/%d %H:%M"),
        "rejectionReason": submission.rejection_reason,
        "reviewedBy": submission.reviewer.email if submission.reviewer else None,
        "reviewedAt": (
            submission.reviewed_at.strftime("%Y/%m/%d %H:%M")
            if submission.reviewed_at
            else None
        ),
    }


@transaction.atomic
def approve_kyc_submission(submission_id, reviewer):
    """
    Approves a KYC submission and marks the user as verified.
    """
    submission, reviewer = _reviewable_submission(submission_id, reviewer)

    submission.status = KYCSubmission.Status.APPROVED
    submission.reviewer = reviewer if reviewer.is_authenticated else None
    submission.reviewed_at = timezone.now()
    submission.rejection_reason = ""
    submission.save(
        update_fields=["status", "reviewer", "reviewed_at", "rejection_reason"]
    )

    # Update User verification flag
    user = submission.profile.user
    user.is_verified = True
    user.save(update_fields=["is_verified"])

    logger.info(
        f"KYC {submission.id} for user {user.email} approved by {reviewer.email}"
    )
    return submission


@transaction.atomic
def reject_kyc_submission(
    submission_id, reviewer, reason="المستندات غير واضحة أو غير مطابقة"
):
    """
    Rejects a KYC submission with a mandatory reason.
    """
    submission, reviewer = _reviewable_submission(submission_id, reviewer)

    if not reason.strip():
        raise ValidationError("A rejection reason is required.")

    submission.status = KYCSubmission.Status.REJECTED
    submission.reviewer = reviewer if reviewer.is_authenticated else None
    submission.reviewed_at = timezone.now()
    submission.rejection_reason = reason
    submission.save(
        update_fields=["status", "reviewer", "reviewed_at", "rejection_reason"]
    )

    # Mark user unverified
    user = submission.profile.user
    user.is_verified = False
    user.save(update_fields=["is_verified"])

    logger.info(
        f"KYC {submission.id} for user {user.email} rejected by {reviewer.email}"
    )
    return submission


def _reviewable_submission(submission_id, reviewer):
    from django.contrib.auth import get_user_model
    from core_apps.profiles.models import Profile
    from core_apps.admin_api.permissions import require_staff_actor
    from core_apps.common.idempotency import fingerprint

    try:
        initial = KYCSubmission.objects.select_related("profile").get(id=submission_id)
    except (KYCSubmission.DoesNotExist, ValueError):
        raise NotFound("Identity submission was not found.")
    if initial.profile.user_id == reviewer.pk:
        raise PermissionDenied("Identity decisions require an independent reviewer.")
    list(
        get_user_model()
        .objects.select_for_update()
        .filter(pk__in=[reviewer.pk, initial.profile.user_id])
        .order_by("pk")
    )
    reviewer = require_staff_actor(
        reviewer,
        {
            StaffProfile.RoleName.SYSTEM_OWNER,
            StaffProfile.RoleName.MAIN_ADMIN,
            StaffProfile.RoleName.KYC_REVIEWER,
        },
        lock=True,
    )
    profile = Profile.objects.select_for_update().get(pk=initial.profile_id)
    submission = (
        KYCSubmission.objects.select_for_update()
        .select_related("profile__user")
        .get(pk=initial.pk)
    )
    latest = profile.kyc_submissions.order_by("-created_at", "-pk").first()
    if (
        latest.pk != submission.pk
        or submission.superseded_at
        or submission.status != "pending"
    ):
        raise ValidationError(
            "Only the current pending identity submission can be reviewed."
        )
    if (
        not submission.evidence_digest
        or fingerprint(submission.evidence_snapshot) != submission.evidence_digest
    ):
        raise ValidationError("Versioned identity evidence is required before review.")
    if not all(
        submission.evidence_snapshot.get(field)
        for field in ("national_id", "id_face", "id_back")
    ):
        raise ValidationError("Complete identity evidence is required before review.")
    return submission, reviewer
