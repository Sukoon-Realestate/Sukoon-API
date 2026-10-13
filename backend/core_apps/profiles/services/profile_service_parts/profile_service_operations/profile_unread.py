"""ProfileUnread operations owned by ProfileService."""

from typing import Any, Dict


class ProfileUnreadMixin:
    @classmethod
    def get_owner_unread_counts(cls, user: Any) -> Dict[str, int]:
        """
        Calculates badge / unread counts for an owner account.
        """
        from django.db.models import Sum
        from core_apps.properties.models import PropertyVisit
        from core_apps.notifications.models import Notification
        from core_apps.chat.models.conversation import ConversationParticipant

        visit_requests_count = PropertyVisit.objects.filter(
            property__owner=user, status=PropertyVisit.Status.PENDING
        ).count()
        unread_notifications_count = Notification.objects.filter(
            user=user, is_read=False
        ).count()
        unread_chat_messages_count = (
            ConversationParticipant.objects.filter(user=user).aggregate(
                total=Sum("unread_count")
            )["total"]
            or 0
        )
        return {
            "visit_requests_count": visit_requests_count,
            "unread_chat_messages_count": unread_chat_messages_count,
            "unread_notifications_count": unread_notifications_count,
        }

    @classmethod
    def get_tenant_unread_counts(cls, user: Any) -> Dict[str, int]:
        """
        Calculates badge / unread counts for a tenant account.
        """
        from django.db.models import Sum
        from core_apps.properties.models import PropertyVisit, SavedProperty
        from core_apps.notifications.models import Notification
        from core_apps.chat.models.conversation import ConversationParticipant

        favorites_count = SavedProperty.objects.filter(user=user).count()
        visit_requests_count = PropertyVisit.objects.filter(
            tenant=user,
            status__in=[PropertyVisit.Status.PENDING, PropertyVisit.Status.CONFIRMED],
        ).count()
        unread_notifications_count = Notification.objects.filter(
            user=user, is_read=False
        ).count()
        unread_chat_messages_count = (
            ConversationParticipant.objects.filter(user=user).aggregate(
                total=Sum("unread_count")
            )["total"]
            or 0
        )
        return {
            "favorites_count": favorites_count,
            "unread_chat_messages_count": unread_chat_messages_count,
            "unread_notifications_count": unread_notifications_count,
            "visit_requests_count": visit_requests_count,
        }
