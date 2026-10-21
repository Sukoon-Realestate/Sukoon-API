"""Policy disposition is separate from publication, inventory and lease state."""

from django.utils.translation import get_language
from .policy import ACTIVE_RESTRICTIONS, BLOCKED_AR, BLOCKED_EN
from core_apps.chat.models import AccountRestriction


class PropertyPolicyProjection:
    def to_representation(self, instance):
        blocked = getattr(instance, "_policy_owner_restricted", None)
        if blocked is None:
            blocked = AccountRestriction.objects.filter(
                user_id=instance.owner_id, state__in=ACTIVE_RESTRICTIONS
            ).exists()
        if blocked:
            request = self.context.get("request")
            viewer = getattr(request, "user", None)
            if not viewer or not (viewer.pk == instance.owner_id or viewer.is_staff):
                return {
                    "id": str(instance.id),
                    "status": "policy_blocked",
                    "title": (
                        BLOCKED_AR
                        if (get_language() or "ar").startswith("ar")
                        else BLOCKED_EN
                    ),
                    "policy_disposition": "under_review",
                    "available": False,
                }
            result = super().to_representation(instance)
            result["policy_disposition"] = "under_review"
            return result
        return super().to_representation(instance)
