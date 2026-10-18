"""ProfileStatus operations owned by ProfileService."""

from typing import Any, Dict
from core_apps.profiles.models import Profile
from ..arabic_months import format_arabic_month_year, format_arabic_count


class ProfileStatusMixin:
    @classmethod
    def get_account_summary_data(cls, user: Any) -> Dict[str, Any]:
        """
        Aggregates data for Screen 2: 'ملخص الحساب' (Account Summary).
        """
        from core_apps.properties.models import (
            PropertyVisit,
            PropertyVisitDecision,
            SavedProperty,
        )
        from core_apps.chat.models import Conversation

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
        total_visits = PropertyVisit.objects.filter(tenant=user).count()
        completed_visits_count = (
            PropertyVisitDecision.objects.filter(tenant=user, attended=True)
            .values("visit_id")
            .distinct()
            .count()
        )
        active_chats_count = (
            Conversation.objects.filter(kind="direct", participant_set__user=user)
            .distinct()
            .count()
        )

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
    def get_verification_status(cls, user: Any) -> Dict[str, Any]:
        """
        Returns shared identity verification status for the authenticated user.
        Allowed statuses: incomplete, pending, approved, rejected.
        """
        from core_apps.admin_api.models import KYCSubmission

        profile, _ = Profile.objects.get_or_create(user=user)
        full_name = user.get_full_name or user.first_name or user.email

        latest_submission = (
            KYCSubmission.objects.filter(profile=profile)
            .order_by("-created_at")
            .first()
        )

        if latest_submission:
            if latest_submission.status == KYCSubmission.Status.APPROVED:
                return {
                    "status": "approved",
                    "full_name": full_name,
                    "submitted_at": latest_submission.created_at.isoformat(),
                    "rejection_reason": "",
                }
            elif latest_submission.status == KYCSubmission.Status.REJECTED:
                return {
                    "status": "rejected",
                    "full_name": full_name,
                    "submitted_at": latest_submission.created_at.isoformat(),
                    "rejection_reason": latest_submission.rejection_reason
                    or "تم رفض المستندات، يرجى إعادة المحاولة.",
                }
            elif latest_submission.status == KYCSubmission.Status.PENDING:
                return {
                    "status": "pending",
                    "full_name": full_name,
                    "submitted_at": latest_submission.created_at.isoformat(),
                    "rejection_reason": "",
                }

        return {
            "status": "incomplete",
            "full_name": full_name,
            "submitted_at": None,
            "rejection_reason": "",
        }
