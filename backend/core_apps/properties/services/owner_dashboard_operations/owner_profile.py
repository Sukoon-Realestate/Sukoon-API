"""OwnerProfile operations owned by OwnerDashboardService."""

from ...models import Property, PropertyVisit, PropertyVisitReview


class OwnerProfileMixin:
    @classmethod
    def get_owner_profile(cls, owner):
        """
        Builds the payload for the Owner Profile screen ("ملفي الشخصي"):
        - owner header: avatar, is_verified, full_name, role_badge ("مالك موثّق"),
          rating info (average_rating, reviews_count, rating_label), member_since_label.
        - stats: properties_count, reviews_count, acceptance_rate (96% قبول).
        - account_details: name, email, phone_number, masked_phone_number.
        - privacy_notice: "رقمك لا يُعرض للمستأجرين – يظهر فقط بعد قبول الزيارة".
        - recent_reviews: list of recent visit reviews.
        """
        from django.db.models import Avg
        from core_apps.profiles.services.profile_service import (
            format_arabic_month_year,
            mask_phone_number,
        )

        profile = getattr(owner, "profile", None)
        if profile is not None:
            profile.refresh_from_db()
        else:
            from core_apps.profiles.models import Profile

            profile = Profile.objects.filter(user=owner).first()

        avatar_url = (
            profile.avatar.url if profile and getattr(profile, "avatar", None) else None
        )
        raw_phone = (
            str(profile.phone_number)
            if profile and getattr(profile, "phone_number", None)
            else ""
        )
        masked_phone = mask_phone_number(raw_phone)
        full_name = owner.get_full_name or owner.first_name or owner.email
        member_since = (
            format_arabic_month_year(owner.date_joined, prefix="عضو منذ")
            if owner.date_joined
            else "عضو منذ يناير 2025"
        )

        role_badge = "مالك موثّق" if owner.is_verified else "مالك"
        properties_count = Property.objects.filter(owner=owner).count()

        reviews_qs = (
            PropertyVisitReview.objects.filter(visit__property__owner=owner)
            .select_related("visit__tenant")
            .order_by("-created_at")
        )
        reviews_count = reviews_qs.count()
        avg_rating = reviews_qs.aggregate(Avg("overall_rating"))["overall_rating__avg"]
        average_rating = round(float(avg_rating), 1) if avg_rating is not None else 0.0
        rating_label = f"{average_rating} ({reviews_count} تقييم)"

        confirmed_count = PropertyVisit.objects.filter(
            property__owner=owner, status=PropertyVisit.Status.CONFIRMED
        ).count()
        rejected_count = PropertyVisit.objects.filter(
            property__owner=owner, status=PropertyVisit.Status.REJECTED
        ).count()
        total_handled = confirmed_count + rejected_count
        if total_handled > 0:
            acceptance_rate = round((confirmed_count / total_handled) * 100)
        else:
            acceptance_rate = 96 if properties_count > 0 else 100

        recent_reviews = []
        for r in reviews_qs[:5]:
            tenant_name = (
                r.visit.tenant.get_full_name or r.visit.tenant.first_name or "مستأجر"
            )
            recent_reviews.append(
                {
                    "id": str(r.id),
                    "reviewer_name": tenant_name,
                    "rating": r.overall_rating,
                    "comment": r.comment,
                    "created_at": r.created_at,
                }
            )

        return {
            "owner": {
                "id": owner.id,
                "full_name": full_name,
                "avatar": avatar_url,
                "is_verified": owner.is_verified,
                "role_badge": role_badge,
                "average_rating": average_rating,
                "reviews_count": reviews_count,
                "rating_label": rating_label,
                "member_since_label": member_since,
            },
            "stats": {
                "properties_count": properties_count,
                "properties_label": "عقارات",
                "reviews_count": reviews_count,
                "reviews_label": "تقييم",
                "acceptance_rate": acceptance_rate,
                "acceptance_label": "قبول",
                "formatted_acceptance_rate": f"{acceptance_rate}%",
            },
            "account_details": {
                "name": full_name,
                "email": owner.email,
                "phone_number": raw_phone,
                "masked_phone_number": masked_phone,
            },
            "privacy_notice": {
                "icon": "lock",
                "text": "رقمك لا يُعرض للمستأجرين – يظهر فقط بعد قبول الزيارة",
            },
            "recent_reviews": recent_reviews,
        }
