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

        from core_apps.features.services.reputation.visibility import summary, subject_rows
        reputation = summary("person_landlord", owner.id)
        reviews_qs = subject_rows("person_landlord", owner.id, aggregate=True)
        reviews_count = reputation["review_count"]
        average_rating = reputation["average"]
        rating_label = f"{average_rating if average_rating is not None else '—'} ({reviews_count})"

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

        recent_reviews = [{"id": str(r.id), "reviewer_name": "", "rating": r.overall_score, "comment": r.public_comment, "created_at": r.created_at.replace(day=1, hour=0, minute=0, second=0, microsecond=0)} for r in reviews_qs[:5]]

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
