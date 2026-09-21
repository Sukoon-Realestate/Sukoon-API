import logging
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, NotFound
from core_apps.admin_api.models import KYCSubmission

logger = logging.getLogger(__name__)


def get_kyc_queue_queryset():
    """
    Returns queryset of KYC submissions optimized with related profile and user data.
    """
    return (
        KYCSubmission.objects.select_related("profile", "profile__user", "reviewer")
        .order_by("-created_at")
    )


def get_kyc_metrics():
    """
    Returns statistical metrics for KYC requests processed today and pending.
    """
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    pending_count = KYCSubmission.objects.filter(status=KYCSubmission.Status.PENDING).count()
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
        submission = (
            KYCSubmission.objects.select_related("profile", "profile__user", "reviewer")
            .get(id=submission_id)
        )
    except (KYCSubmission.DoesNotExist, ValueError):
        raise NotFound(f"KYC Submission with ID {submission_id} was not found.")

    user = submission.profile.user
    profile = submission.profile
    is_owner = user.properties.exists()

    return {
        "id": str(submission.id),
        "user_id": str(user.id),
        "userName": user.get_full_name or user.email,
        "userEmail": user.email,
        "userPhone": str(profile.phone_number) if profile.phone_number else "غير متوفر",
        "userType": "مالك" if is_owner else "مستأجر",
        "nationalId": profile.national_id or "غير مسجل",
        "birthDate": profile.birth_date.strftime("%Y/%m/%d") if profile.birth_date else "غير محدد",
        "gender": profile.get_gender_display() if hasattr(profile, "get_gender_display") else "غير محدد",
        "idFaceUrl": profile.id_face.url if profile.id_face else None,
        "idBackUrl": profile.id_back.url if profile.id_back else None,
        "selfieUrl": profile.confirmation_selfi.url if profile.confirmation_selfi else None,
        "status": submission.status,
        "statusDisplay": submission.get_status_display(),
        "submittedAt": submission.created_at.strftime("%Y/%m/%d %H:%M"),
        "rejectionReason": submission.rejection_reason,
        "reviewedBy": submission.reviewer.email if submission.reviewer else None,
        "reviewedAt": submission.reviewed_at.strftime("%Y/%m/%d %H:%M") if submission.reviewed_at else None,
    }


@transaction.atomic
def approve_kyc_submission(submission_id, reviewer):
    """
    Approves a KYC submission and marks the user as verified.
    """
    try:
        submission = KYCSubmission.objects.select_related("profile__user").get(id=submission_id)
    except (KYCSubmission.DoesNotExist, ValueError):
        raise NotFound(f"KYC Submission with ID {submission_id} was not found.")

    if submission.status == KYCSubmission.Status.APPROVED:
        raise ValidationError("This KYC submission has already been approved.")

    submission.status = KYCSubmission.Status.APPROVED
    submission.reviewer = reviewer if reviewer.is_authenticated else None
    submission.reviewed_at = timezone.now()
    submission.rejection_reason = ""
    submission.save(update_fields=["status", "reviewer", "reviewed_at", "rejection_reason"])

    # Update User verification flag
    user = submission.profile.user
    user.is_verified = True
    user.save(update_fields=["is_verified"])

    logger.info(f"KYC {submission.id} for user {user.email} approved by {reviewer.email}")
    return submission


@transaction.atomic
def reject_kyc_submission(submission_id, reviewer, reason="المستندات غير واضحة أو غير مطابقة"):
    """
    Rejects a KYC submission with a mandatory reason.
    """
    try:
        submission = KYCSubmission.objects.select_related("profile__user").get(id=submission_id)
    except (KYCSubmission.DoesNotExist, ValueError):
        raise NotFound(f"KYC Submission with ID {submission_id} was not found.")

    if not reason.strip():
        raise ValidationError("A rejection reason is required.")

    submission.status = KYCSubmission.Status.REJECTED
    submission.reviewer = reviewer if reviewer.is_authenticated else None
    submission.reviewed_at = timezone.now()
    submission.rejection_reason = reason
    submission.save(update_fields=["status", "reviewer", "reviewed_at", "rejection_reason"])

    # Mark user unverified
    user = submission.profile.user
    user.is_verified = False
    user.save(update_fields=["is_verified"])

    logger.info(f"KYC {submission.id} for user {user.email} rejected by {reviewer.email}")
    return submission
