"""Private authenticated account projection; never public owner-card data."""
from core_apps.features.services.billing_catalog import subscription_summary


def journey_summary(user):
    profile = getattr(user, "profile", None)
    # Match complete_user_registration's existing completeness rule. Submission
    # completeness is separate from the authoritative verification decision.
    complete = bool(profile and profile.national_id and profile.id_face and profile.id_back)
    return {"is_subscriped": True, "subscription_summary": subscription_summary(user),
            "has_completed_registration": complete, "available_workspaces": ["tenant", "owner"]}


def canonical_user(user):
    return {"id": str(user.id), "email": user.email, "first_name": user.first_name,
            "last_name": user.last_name, "full_name": user.get_full_name,
            "phone_number": str(getattr(getattr(user, "profile", None), "phone_number", "") or ""),
            "is_verified": user.is_verified, **journey_summary(user)}


class PrivateJourneySerializerMixin:
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        identity = str(instance.get("id", "")) if isinstance(instance, dict) else str(instance.id)
        if user and user.is_authenticated and identity == str(user.id):
            data.update(journey_summary(user))
        return data
