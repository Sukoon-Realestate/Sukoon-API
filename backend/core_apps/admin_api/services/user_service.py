import logging
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, NotFound
from core_apps.admin_api.models import UserReport, KYCSubmission

logger = logging.getLogger(__name__)
User = get_user_model()


def get_admin_users_queryset():
    """
    Returns optimized queryset for admin user management with aggregated counts.
    """
    return (
        User.objects.select_related("profile")
        .prefetch_related("properties", "profile__kyc_submissions", "reports_received")
        .annotate(
            properties_count=Count("properties", distinct=True),
            visit_requests_count=Count("visits", distinct=True),
            reports_count=Count("reports_received", distinct=True),
        )
        .order_by("-date_joined")
    )


import uuid
from django.core.exceptions import ValidationError as DjangoValidationError


def _get_user_by_identifier(user_id, prefetch=False):
    """
    Resolve the canonical account identity. Names and emails are not commands.
    """
    str_id = str(user_id).strip()
    qs = User.objects.none()

    # 1. Try UUID
    try:
        uuid_obj = uuid.UUID(str_id)
        qs = User.objects.filter(id=uuid_obj)
    except (ValueError, TypeError, AttributeError):
        raise NotFound("A canonical user UUID is required.")

    if prefetch:
        qs = qs.select_related("profile").prefetch_related(
            "properties", "visits", "reports_received", "profile__kyc_submissions"
        )

    user = qs.first()
    if not user:
        raise NotFound(f"User with identifier '{user_id}' was not found.")
    return user


def get_admin_user_detail(user_id):
    """
    Returns complete user profile and related activity logs for the admin details screen.
    """
    user = _get_user_by_identifier(user_id, prefetch=True)

    profile = getattr(user, "profile", None)

    # Determine user role/type
    is_owner = user.properties.exists()
    user_type = "مالك" if is_owner else "مستأجر"

    # Determine KYC status
    latest_kyc = (
        profile.kyc_submissions.order_by("-created_at").first() if profile else None
    )
    if latest_kyc:
        if latest_kyc.status == KYCSubmission.Status.APPROVED:
            kyc_status = "موثق"
        elif latest_kyc.status == KYCSubmission.Status.PENDING:
            kyc_status = "قيد المراجعة"
        else:
            kyc_status = "مرفوض"
    else:
        kyc_status = "موثق" if user.is_verified else "قيد المراجعة"

    # Status label
    if not user.is_active:
        user_status = "موقوف"
    elif user.is_verified:
        user_status = "نشط"
    else:
        user_status = "قيد المراجعة"

    # Build activity log
    activity_log = []
    for vr in user.visits.order_by("-created_at")[:5]:
        activity_log.append(
            {
                "id": f"vr-{vr.id}",
                "title": f"طلب معاينة لعقار #{vr.property.title if hasattr(vr, 'property') else ''}",
                "time": vr.created_at.strftime("%Y-%m-%d %H:%M"),
                "type": "visit",
            }
        )
    if profile:
        for kyc in profile.kyc_submissions.order_by("-created_at")[:3]:
            activity_log.append(
                {
                    "id": f"kyc-{kyc.id}",
                    "title": f"تحديث حالة التوثيق إلى: {kyc.get_status_display()}",
                    "time": kyc.created_at.strftime("%Y-%m-%d %H:%M"),
                    "type": "kyc",
                }
            )

    return {
        "id": str(user.id),
        "name": user.get_full_name or user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "type": user_type,
        "status": user_status,
        "kycStatus": kyc_status,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "regDate": user.date_joined.strftime("%Y/%m/%d"),
        "phone": (
            str(profile.phone_number)
            if profile and profile.phone_number
            else "غير متوفر"
        ),
        "national_id": profile.national_id if profile else "",
        "avatar": profile.avatar.url if profile and profile.avatar else None,
        "visitRequests": user.visits.count(),
        "properties_count": user.properties.count(),
        "reportsAgainst": user.reports_received.count(),
        "activityLog": activity_log,
    }


@transaction.atomic
def suspend_user(user_id, admin_user, reason="إيقاف إداري"):
    """
    Suspends a user account and logs the action.
    """
    from core_apps.admin_api.permissions import require_staff_actor

    require_staff_actor(admin_user, {"system_owner", "main_admin"}, lock=True)
    user = _get_user_by_identifier(user_id)
    if user.is_superuser or hasattr(user, "staff_profile"):
        raise ValidationError(
            "Use staff authority management for administrative accounts."
        )
    user = User.objects.select_for_update().get(pk=user.pk)

    if not user.is_active:
        raise ValidationError("User account is already suspended.")

    user.is_active = False
    user.save(update_fields=["is_active"])
    from core_apps.users.services.sessions import revoke_all

    user = revoke_all(user, actor=admin_user, action="account.admin_suspended")

    UserReport.objects.create(
        reported_user=user,
        reporter=admin_user if admin_user.is_authenticated else None,
        reason=reason or "إيقاف إداري للحساب",
        reason_type=UserReport.ReasonType.OTHER,
        status=UserReport.Status.SUSPENDED,
        automation_level=UserReport.AutomationLevel.LOW,
        reviewed_by=admin_user if admin_user.is_authenticated else None,
        notes=f"تم إيقاف الحساب بواسطة {admin_user.email}",
    )

    logger.info(f"User {user.email} suspended by {admin_user.email}")
    return user


@transaction.atomic
def unsuspend_user(user_id, admin_user):
    """
    Reactivates a suspended user account.
    """
    from core_apps.admin_api.permissions import require_staff_actor

    require_staff_actor(admin_user, {"system_owner", "main_admin"}, lock=True)
    user = _get_user_by_identifier(user_id)
    if user.is_superuser or hasattr(user, "staff_profile"):
        raise ValidationError(
            "Use staff authority management for administrative accounts."
        )
    user = User.objects.select_for_update().get(pk=user.pk)

    if user.closed_at is not None:
        raise ValidationError("A completed account deletion cannot be reactivated.")

    if user.is_active:
        raise ValidationError("User account is already active.")

    user.is_active = True
    user.save(update_fields=["is_active"])

    # Update any active suspension reports
    UserReport.objects.filter(
        reported_user=user, status=UserReport.Status.SUSPENDED
    ).update(status=UserReport.Status.ACTIVE)

    logger.info(f"User {user.email} reactivated by {admin_user.email}")
    return user
