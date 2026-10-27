"""ProfileAccount operations owned by ProfileService."""

from typing import Any, Dict, Optional
from core_apps.profiles.models import Contract, Profile
from ..arabic_months import ARABIC_MONTHS, format_arabic_month_year, format_arabic_count


class ProfileAccountMixin:
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
            if profile.avatar:
                score += 20
            if user.is_verified or profile.national_id or profile.id_face:
                score += 10
        elif user.is_verified:
            score += 10

        return min(round(score * 100 / 75), 100)

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
        contracts_count = Contract.objects.filter(
            tenant=user, status=Contract.Status.ACTIVE
        ).count()

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
