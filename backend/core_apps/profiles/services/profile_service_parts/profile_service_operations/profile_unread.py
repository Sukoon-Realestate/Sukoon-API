"""ProfileUnread operations owned by ProfileService."""

from typing import Any, Dict


class ProfileUnreadMixin:
    @classmethod
    def get_owner_unread_counts(cls, user: Any) -> Dict[str, Any]:
        """
        Calculates badge / unread counts for an owner account.
        """
        from core_apps.chat.services.group_access import total_unread_count
        from core_apps.properties.models import PropertyVisit
        from core_apps.notifications.services import NotificationService
        from core_apps.features.services.request_counts import pending_request_counts

        visit_requests_count = PropertyVisit.objects.filter(
            property__owner=user, status=PropertyVisit.Status.PENDING
        ).count()
        unread_notifications_count = NotificationService.get_unread_count(user, scope="owner")
        unread_chat_messages_count = total_unread_count(user)
        return {
            "request_counts": pending_request_counts(user, owner=True),
            "visit_requests_count": visit_requests_count,
            "unread_chat_messages_count": unread_chat_messages_count,
            "unread_notifications_count": unread_notifications_count,
        }

    @classmethod
    def get_tenant_unread_counts(cls, user: Any, *, scope="individual") -> Dict[str, Any]:
        """
        Calculates badge / unread counts for a tenant account.
        """
        from core_apps.chat.services.group_access import total_unread_count
        from core_apps.properties.models import PropertyVisit, SavedProperty
        from core_apps.notifications.services import NotificationService
        from core_apps.features.planning_models import GroupJoinRequest
        from core_apps.features.services.request_counts import (
            pending_request_counts,
            company_approval_counts,
        )

        favorites_count = SavedProperty.objects.filter(user=user).count()
        group_join_requests_count = (
            GroupJoinRequest.objects.filter(
                status="pending",
                group__status="active",
                group__memberships__user=user,
                group__memberships__role="admin",
                group__memberships__status="active",
            )
            .distinct()
            .count()
        )
        visit_requests_count = PropertyVisit.objects.filter(
            tenant=user,
            status__in=[PropertyVisit.Status.PENDING, PropertyVisit.Status.CONFIRMED],
        ).count()
        unread_notifications_count = NotificationService.get_unread_count(user, scope=scope)
        unread_chat_messages_count = total_unread_count(user)
        return {
            "request_counts": pending_request_counts(user),
            "company_approval_counts": company_approval_counts(user),
            "favorites_count": favorites_count,
            "group_join_requests_count": group_join_requests_count,
            "unread_chat_messages_count": unread_chat_messages_count,
            "unread_notifications_count": unread_notifications_count,
            "visit_requests_count": visit_requests_count,
        }
