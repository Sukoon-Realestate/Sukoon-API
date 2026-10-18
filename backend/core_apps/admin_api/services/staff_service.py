import logging
import uuid
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from core_apps.admin_api.models import StaffProfile, StaffAuthorityAudit

logger = logging.getLogger(__name__)
User = get_user_model()

DEFAULT_PERMISSIONS_MATRIX = [
    {
        "action": "مراجعة طلبات التوثيق KYC",
        "systemOwner": True,
        "mainAdmin": True,
        "kycReviewer": True,
        "propertyReviewer": False,
        "support": False,
    },
    {
        "action": "قبول ورفض العقارات الجديدة",
        "systemOwner": True,
        "mainAdmin": True,
        "kycReviewer": False,
        "propertyReviewer": True,
        "support": False,
    },
    {
        "action": "إيقاف وحظر حسابات المستخدمين",
        "systemOwner": True,
        "mainAdmin": True,
        "kycReviewer": False,
        "propertyReviewer": False,
        "support": False,
    },
    {
        "action": "تعديل أدوار وصلاحيات الفريق",
        "systemOwner": True,
        "mainAdmin": False,
        "kycReviewer": False,
        "propertyReviewer": False,
        "support": False,
    },
    {
        "action": "إرسال إشعارات جماعية للمستخدمين",
        "systemOwner": False,
        "mainAdmin": False,
        "kycReviewer": False,
        "propertyReviewer": False,
        "support": False,
    },
    {
        "action": "تعديل تفضيلات لوحة الإدارة",
        "systemOwner": True,
        "mainAdmin": False,
        "kycReviewer": False,
        "propertyReviewer": False,
        "support": False,
    },
]


def get_staff_queryset():
    """
    Returns queryset of active staff profiles with associated user accounts.
    """
    return (
        StaffProfile.objects.filter(is_active=True)
        .select_related("user")
        .order_by("-created_at")
    )


def get_roles_summary():
    """
    Returns summary statistics for each defined staff role.
    """
    roles_meta = [
        {
            "id": "system_owner",
            "name": "مالك النظام (Owner)",
            "subtext": "إدارة الفريق والمنصة مع الالتزام بضوابط الاستقلال والسياسات",
            "userCount": StaffProfile.objects.filter(
                role_name="system_owner", is_active=True
            ).count(),
            "color": "bg-rose-500",
            "badges": ["وصول كامل", "صلاحيات أمنية"],
        },
        {
            "id": "main_admin",
            "name": "مشرف رئيسي (Main Admin)",
            "subtext": "إدارة العمليات والمحتوى والمستخدمين",
            "userCount": StaffProfile.objects.filter(
                role_name="main_admin", is_active=True
            ).count(),
            "color": "bg-teal-500",
            "badges": ["إدارة المستخدمين", "العقارات"],
        },
        {
            "id": "kyc_reviewer",
            "name": "مراجع KYC",
            "subtext": "فحص الهويات والتحقق من المستخدمين",
            "userCount": StaffProfile.objects.filter(
                role_name="kyc_reviewer", is_active=True
            ).count(),
            "color": "bg-blue-500",
            "badges": ["فحص المستندات"],
        },
        {
            "id": "property_reviewer",
            "name": "مراجع عقارات",
            "subtext": "مراجعة إعلانات العقارات والموافقة",
            "userCount": StaffProfile.objects.filter(
                role_name="property_reviewer", is_active=True
            ).count(),
            "color": "bg-amber-500",
            "badges": ["مراجعة العقارات"],
        },
        {
            "id": "support",
            "name": "دعم العملاء",
            "subtext": "استقبال التذاكر والرد على الاستفسارات",
            "userCount": StaffProfile.objects.filter(
                role_name="support", is_active=True
            ).count(),
            "color": "bg-purple-500",
            "badges": ["التذاكر"],
        },
    ]
    labels = {
        "financial_approver": "معتمد مالي",
        "psp_reconciliation": "مطابقة مزود الدفع",
        "payout_operator": "مشغل التحويلات",
        "refund_operator": "مشغل الاسترداد",
        "dispute_resolver": "مسؤول تسوية النزاعات",
    }
    for role, label in labels.items():
        roles_meta.append(
            {
                "id": role,
                "name": label,
                "subtext": "صلاحية تشغيلية تخضع للتحقق والسياسة المعتمدة",
                "userCount": StaffProfile.objects.filter(
                    role_name=role, is_active=True
                ).count(),
                "color": "bg-slate-500",
                "badges": ["صلاحية محددة"],
            }
        )
    return roles_meta


@transaction.atomic
def invite_staff_member(email, name, role_name, *, actor, reason):
    """
    Creates a new staff account or links an existing user to a StaffProfile.
    """
    actor = _lock_authority(actor)
    reason = _reason(reason)
    if role_name not in StaffProfile.RoleName.values:
        raise ValidationError({"role_name": "Select a supported administrative role."})
    if email.strip().casefold() == actor.email.casefold():
        raise PermissionDenied("An administrator cannot change their own authority.")
    if not email:
        raise ValidationError("Email address is required.")
    if not name:
        raise ValidationError("Staff name is required.")

    name_parts = name.strip().split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    user, created = User.objects.get_or_create(
        email=email.lower().strip(),
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "is_staff": True,
            "is_verified": False,
        },
    )

    if user.is_superuser:
        raise PermissionDenied(
            "Superuser authority cannot be changed through staff invitations."
        )
    before = _snapshot(StaffProfile.objects.filter(user=user).first())

    if not created:
        user.first_name = first_name
        if last_name:
            user.last_name = last_name
        user.is_staff = True
        user.save(update_fields=["first_name", "last_name", "is_staff"])

    role_mapping = {
        "مالك النظام": "system_owner",
        "مشرف رئيسي": "main_admin",
        "مراجع KYC": "kyc_reviewer",
        "مراجع عقارات": "property_reviewer",
        "دعم العملاء": "support",
    }
    canonical_role = role_mapping.get(role_name, role_name)

    staff_profile, _ = StaffProfile.objects.update_or_create(
        user=user,
        defaults={
            "role_name": canonical_role,
            "display_role": role_name,
            "is_active": True,
        },
    )

    logger.info(f"Staff member {email} created/updated with role {canonical_role}")
    StaffAuthorityAudit.objects.create(
        actor=actor,
        target=user,
        action="grant",
        before=before,
        after=_snapshot(staff_profile),
        reason=reason,
    )
    return staff_profile


@transaction.atomic
def remove_staff_member(staff_id, *, actor, reason):
    """
    Deactivates a staff member and removes admin privileges.
    """
    actor = _lock_authority(actor)
    reason = _reason(reason)
    try:
        staff_profile = StaffProfile.objects.select_related("user").get(id=staff_id)
    except (StaffProfile.DoesNotExist, ValueError):
        raise NotFound(f"Staff profile with ID {staff_id} was not found.")

    if staff_profile.user_id == actor.pk or staff_profile.user.is_superuser:
        raise PermissionDenied(
            "Self-revocation and superuser changes require a separate authority process."
        )
    before = _snapshot(staff_profile)
    staff_profile.is_active = False
    staff_profile.save(update_fields=["is_active"])

    user = staff_profile.user
    user.is_staff = False
    user.save(update_fields=["is_staff"])

    logger.info(f"Staff member {user.email} removed from staff privileges")
    StaffAuthorityAudit.objects.create(
        actor=actor,
        target=user,
        action="revoke",
        before=before,
        after=_snapshot(staff_profile),
        reason=reason,
    )
    return staff_profile


def _lock_authority(actor):
    # Role changes are rare. Lock the administrative cohort in a stable order,
    # using the same user-before-profile order as financial commands. This
    # serializes two owners revoking one another and prevents cached authority.
    from django.db.models import Q
    from core_apps.admin_api.permissions import require_staff_actor

    list(
        User.objects.select_for_update(of=("self",))
        .filter(Q(staff_profile__isnull=False) | Q(is_superuser=True) | Q(pk=actor.pk))
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    list(
        StaffProfile.objects.select_for_update()
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    return require_staff_actor(actor, {StaffProfile.RoleName.SYSTEM_OWNER}, lock=True)


def _reason(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 500:
        raise ValidationError(
            {"reason": "Supply an administrative reason of 1–500 characters."}
        )
    return value.strip()


def _snapshot(profile):
    return {"role": profile.role_name, "active": profile.is_active} if profile else {}
