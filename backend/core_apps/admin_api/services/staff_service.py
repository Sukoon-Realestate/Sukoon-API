import logging
import uuid
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, NotFound
from core_apps.admin_api.models import StaffProfile

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
        "systemOwner": True,
        "mainAdmin": True,
        "kycReviewer": False,
        "propertyReviewer": False,
        "support": True,
    },
    {
        "action": "تعديل إعدادات النظام وقواعد الأتمتة",
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
            "subtext": "كافة الصلاحيات غير المقيدة",
            "userCount": StaffProfile.objects.filter(role_name="system_owner", is_active=True).count(),
            "color": "bg-rose-500",
            "badges": ["وصول كامل", "صلاحيات أمنية"],
        },
        {
            "id": "main_admin",
            "name": "مشرف رئيسي (Main Admin)",
            "subtext": "إدارة العمليات والمحتوى والمستخدمين",
            "userCount": StaffProfile.objects.filter(role_name="main_admin", is_active=True).count(),
            "color": "bg-teal-500",
            "badges": ["إدارة المستخدمين", "العقارات"],
        },
        {
            "id": "kyc_reviewer",
            "name": "مراجع KYC",
            "subtext": "فحص الهويات والتحقق من المستخدمين",
            "userCount": StaffProfile.objects.filter(role_name="kyc_reviewer", is_active=True).count(),
            "color": "bg-blue-500",
            "badges": ["فحص المستندات"],
        },
        {
            "id": "property_reviewer",
            "name": "مراجع عقارات",
            "subtext": "مراجعة إعلانات العقارات والموافقة",
            "userCount": StaffProfile.objects.filter(role_name="property_reviewer", is_active=True).count(),
            "color": "bg-amber-500",
            "badges": ["مراجعة العقارات"],
        },
        {
            "id": "support",
            "name": "دعم العملاء",
            "subtext": "استقبال التذاكر والرد على الاستفسارات",
            "userCount": StaffProfile.objects.filter(role_name="support", is_active=True).count(),
            "color": "bg-purple-500",
            "badges": ["التذاكر"],
        },
    ]
    return roles_meta


@transaction.atomic
def invite_staff_member(email, name, role_name):
    """
    Creates a new staff account or links an existing user to a StaffProfile.
    """
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
            "is_verified": True,
        },
    )

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
    return staff_profile


@transaction.atomic
def remove_staff_member(staff_id):
    """
    Deactivates a staff member and removes admin privileges.
    """
    try:
        staff_profile = StaffProfile.objects.select_related("user").get(id=staff_id)
    except (StaffProfile.DoesNotExist, ValueError):
        raise NotFound(f"Staff profile with ID {staff_id} was not found.")

    staff_profile.is_active = False
    staff_profile.save(update_fields=["is_active"])

    user = staff_profile.user
    user.is_staff = False
    user.save(update_fields=["is_staff"])

    logger.info(f"Staff member {user.email} removed from staff privileges")
    return staff_profile
