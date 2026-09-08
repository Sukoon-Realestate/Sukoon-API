import logging
from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model
from django.db import transaction

from core_apps.profiles.models import Profile, UserSettings

logger = logging.getLogger(__name__)
User = get_user_model()

# * Arabic month names mapping
ARABIC_MONTHS = {
    1: "يناير",
    2: "فبراير",
    3: "مارس",
    4: "أبريل",
    5: "مايو",
    6: "يونيو",
    7: "يوليو",
    8: "أغسطس",
    9: "سبتمبر",
    10: "أكتوبر",
    11: "نوفمبر",
    12: "ديسمبر",
}


def mask_phone_number(raw_number: Any) -> str:
    """Mask phone number in format 010****432."""
    if not raw_number:
        return ""
    digits = str(raw_number).strip()
    clean = digits.replace("+2", "").strip() if digits.startswith("+2") else digits
    if len(clean) >= 7:
        return f"{clean[:3]}****{clean[-3:]}"
    return clean


def format_arabic_month_year(dt, prefix: str = "عضو منذ") -> str:
    """Format datetime/date as e.g. 'عضو منذ يناير 2026'."""
    if not dt:
        return f"{prefix} يناير 2026"
    month_name = ARABIC_MONTHS.get(dt.month, "")
    if prefix:
        return f"{prefix} {month_name} {dt.year}".strip()
    return f"{month_name} {dt.year}".strip()


def format_arabic_date(dt) -> str:
    """Format date as e.g. '15 مارس 1995'."""
    if not dt:
        return ""
    month_name = ARABIC_MONTHS.get(dt.month, "")
    return f"{dt.day} {month_name} {dt.year}".strip()


def format_arabic_count(count: int, singular: str, plural: str) -> str:
    """Format count with appropriate singular or plural Arabic noun."""
    if 3 <= count <= 10:
        return f"{count} {plural}"
    return f"{count} {singular}"


class ProfileService:
    """
    Service layer for tenant profile, mobile account screens, and data aggregation.
    """

    @classmethod
    def calculate_profile_completion(
        cls, user: Any, profile: Optional[Profile] = None
    ) -> int:
        """
        Calculates profile completion percentage (0 - 100).
        Weights:
        - Full Name: 15%
        - Email: 15%
        - Phone number: 15%
        - Birth date: 15%
        - Gender: 10%
        - Identity verified (or national ID): 10%
        - Avatar: 20%
        """
        if profile is None:
            profile = getattr(user, "profile", None)

        score = 0
        if user.first_name and user.last_name:
            score += 15
        elif user.first_name or user.last_name:
            score += 8

        if user.email:
            score += 15

        if profile:
            if profile.phone_number:
                score += 15
            if profile.birth_date:
                score += 15
            if profile.gender:
                score += 10
            if profile.avatar:
                score += 20
            if user.is_verified or profile.national_id or profile.id_face:
                score += 10
        elif user.is_verified:
            score += 10

        return min(score, 100)

    @classmethod
    def get_my_account_data(cls, user: Any) -> Dict[str, Any]:
        """
        Aggregates data for Screen 1: 'حسابي' (My Account).
        """
        # ? Avoid circular imports by loading models locally
        from core_apps.properties.models import (
            PropertyVisit,
            PropertyVisitReview,
            SavedProperty,
        )

        profile, _ = Profile.objects.get_or_create(user=user)

        avatar_url = profile.avatar.url if profile.avatar else None
        member_year = user.date_joined.year if user.date_joined else 2026
        member_month = (
            ARABIC_MONTHS.get(user.date_joined.month, "يناير")
            if user.date_joined
            else "يناير"
        )
        member_since_label = format_arabic_month_year(
            user.date_joined, prefix="عضو منذ"
        )

        # * Calculate statistics
        saved_count = SavedProperty.objects.filter(user=user).count()
        visits_count = PropertyVisit.objects.filter(tenant=user).count()
        reviews_count = PropertyVisitReview.objects.filter(visit__tenant=user).count()
        contracts_count = 1 if visits_count > 0 else 0

        verification_label = "موثّق ✓" if user.is_verified else "غير موثّق"

        return {
            "user": {
                "id": user.id,
                "full_name": user.get_full_name or user.first_name or user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "avatar": avatar_url,
                "is_verified": user.is_verified,
                "verification_badge": "موثّق" if user.is_verified else "غير موثّق",
                "role_label": "مستأجر",
                "member_since_label": member_since_label,
                "member_since_year": member_year,
                "member_since_month": member_month,
            },
            "stats": {
                "saved_count": saved_count,
                "visits_count": visits_count,
                "reviews_count": reviews_count,
            },
            "menu_items": {
                "visit_requests": {
                    "title": "طلبات الزيارة",
                    "count": visits_count,
                    "subtitle": format_arabic_count(visits_count, "طلب", "طلبات"),
                },
                "contracts": {
                    "title": "عقودي",
                    "count": contracts_count,
                    "subtitle": f"{contracts_count} عقد نشط",
                },
                "reviews": {
                    "title": "تقييماتي",
                    "count": reviews_count,
                    "subtitle": f"{reviews_count} تقييم",
                },
                "verification": {
                    "title": "التوثيق والخصوصية",
                    "is_verified": user.is_verified,
                    "subtitle": verification_label,
                },
            },
            "account_details": {
                "name": user.get_full_name or user.first_name or user.email,
                "email": user.email,
            },
        }

    @classmethod
    def get_account_summary_data(cls, user: Any) -> Dict[str, Any]:
        """
        Aggregates data for Screen 2: 'ملخص الحساب' (Account Summary).
        """
        from core_apps.properties.models import PropertyVisit, SavedProperty

        profile, _ = Profile.objects.get_or_create(user=user)

        avatar_url = profile.avatar.url if profile.avatar else None
        full_name = user.get_full_name or user.first_name or user.email
        initial = (
            user.first_name[0]
            if user.first_name
            else (user.email[0] if user.email else "م")
        )
        member_since_label = format_arabic_month_year(user.date_joined, prefix="منذ")
        completion_percentage = cls.calculate_profile_completion(user, profile)

        saved_count = SavedProperty.objects.filter(user=user).count()
        confirmed_visits = PropertyVisit.objects.filter(
            tenant=user, status=PropertyVisit.Status.CONFIRMED
        ).count()
        total_visits = PropertyVisit.objects.filter(tenant=user).count()
        completed_visits_count = (
            confirmed_visits if confirmed_visits > 0 else total_visits
        )
        active_chats_count = confirmed_visits

        is_verified = user.is_verified
        id_title = "هويتك موثّقة" if is_verified else "التحقق من الهوية"
        id_subtitle = (
            "تم التحقق من بطاقة الهوية"
            if is_verified
            else "يرجى رفع بطاقة الهوية للتحقق"
        )
        id_status_label = "مكتمل" if is_verified else "غير مكتمل"

        return {
            "user": {
                "id": user.id,
                "full_name": full_name,
                "avatar": avatar_url,
                "initial": initial,
                "role_label": "مستأجر",
                "member_since_label": member_since_label,
                "profile_completion_percentage": completion_percentage,
                "profile_completion_label": "اكتمال الملف",
            },
            "identity_verification": {
                "is_verified": is_verified,
                "title": id_title,
                "subtitle": id_subtitle,
                "status_label": id_status_label,
            },
            "stats": {
                "saved_properties_count": saved_count,
                "completed_visits_count": completed_visits_count,
                "active_chats_count": active_chats_count,
            },
            "shortcuts": {
                "saved_properties": {
                    "title": "العقارات المحفوظة",
                    "count": saved_count,
                    "label": f"{saved_count} عقار",
                },
                "visits_history": {
                    "title": "سجل الزيارات",
                    "count": total_visits,
                    "label": format_arabic_count(total_visits, "زيارة", "زيارات"),
                },
                "identity_verification": {
                    "title": "التحقق من الهوية",
                    "status": "completed" if is_verified else "incomplete",
                    "label": id_status_label,
                },
            },
        }

    @classmethod
    @transaction.atomic
    def update_user_profile(cls, user: Any, validated_data: Dict[str, Any]) -> Profile:
        """
        Updates user and profile fields atomically for Screen 3: 'تعديل الملف'.
        """
        profile, _ = Profile.objects.get_or_create(user=user)

        user_fields_to_update = []

        # * Handle full_name or first_name / last_name
        if "full_name" in validated_data:
            full_name = validated_data.pop("full_name", "").strip()
            parts = full_name.split(maxsplit=1)
            user.first_name = parts[0] if parts else ""
            user.last_name = parts[1] if len(parts) > 1 else ""
            user_fields_to_update.extend(["first_name", "last_name"])

        # * Handle nested user dictionary from serializer source='user.*'
        user_data = validated_data.pop("user", {})
        if isinstance(user_data, dict):
            if "first_name" in user_data:
                user.first_name = user_data["first_name"]
                if "first_name" not in user_fields_to_update:
                    user_fields_to_update.append("first_name")
            if "last_name" in user_data:
                user.last_name = user_data["last_name"]
                if "last_name" not in user_fields_to_update:
                    user_fields_to_update.append("last_name")
            if "email" in user_data:
                new_email = user_data["email"]
                if new_email and new_email != user.email:
                    user.email = new_email
                    user_fields_to_update.append("email")

        if "first_name" in validated_data:
            user.first_name = validated_data.pop("first_name")
            if "first_name" not in user_fields_to_update:
                user_fields_to_update.append("first_name")

        if "last_name" in validated_data:
            user.last_name = validated_data.pop("last_name")
            if "last_name" not in user_fields_to_update:
                user_fields_to_update.append("last_name")

        if "email" in validated_data:
            new_email = validated_data.pop("email")
            if new_email and new_email != user.email:
                user.email = new_email
                user_fields_to_update.append("email")

        if user_fields_to_update:
            user.save(update_fields=list(set(user_fields_to_update)))

        # * Update profile fields (including avatar)
        for field, value in validated_data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)

        profile.save()
        return profile

    @classmethod
    def get_user_settings(cls, user: Any) -> UserSettings:
        """
        Retrieves or initializes settings for the given user.
        """
        settings_obj, _ = UserSettings.objects.get_or_create(user=user)
        return settings_obj

    @classmethod
    @transaction.atomic
    def update_user_settings(
        cls, user: Any, validated_data: Dict[str, Any]
    ) -> UserSettings:
        """
        Updates settings for the given user within an atomic transaction.
        Enforces privacy constraints (e.g. always_hide_mobile_number cannot be disabled).
        """
        settings_obj, _ = UserSettings.objects.get_or_create(user=user)

        # ! Enforce privacy rule: always_hide_mobile_number cannot be turned off
        validated_data.pop("always_hide_mobile_number", None)

        for field, value in validated_data.items():
            if hasattr(settings_obj, field):
                setattr(settings_obj, field, value)

        settings_obj.save()
        return settings_obj
