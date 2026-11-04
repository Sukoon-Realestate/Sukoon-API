"""Counts for active personal workspaces, excluding deferred case contexts."""
from django.db.models import Sum
from rest_framework.exceptions import PermissionDenied


def active_counts(user, scope):
    if scope == 'account':
        from core_apps.notifications.services import NotificationService
        return {'favorites_count': 0, 'visit_requests_count': 0, 'unread_chat_messages_count': 0,
                'unread_notifications_count': NotificationService.get_unread_count(user, scope=scope)}
    if scope not in {'individual', 'owner'}:
        raise PermissionDenied('This workspace is deferred for the MVP release.')
    from core_apps.chat.models import ConversationParticipant
    from core_apps.chat.services.workspace_inbox import scoped
    from core_apps.properties.models import PropertyVisit, SavedProperty
    from core_apps.notifications.services import NotificationService
    visits = PropertyVisit.objects.filter(company__isnull=True,
        academic_plan__isnull=True, groupprocess__isnull=True)
    visits = (visits.filter(property__owner=user, status=PropertyVisit.Status.PENDING)
              if scope == 'owner' else visits.filter(tenant=user,
                  status__in=[PropertyVisit.Status.PENDING, PropertyVisit.Status.CONFIRMED]))
    unread = ConversationParticipant.objects.filter(user=user,
        conversation__in=scoped(user, scope)).aggregate(total=Sum('unread_count'))['total'] or 0
    return {'favorites_count': SavedProperty.objects.filter(user=user).count(),
            'visit_requests_count': visits.count(), 'unread_chat_messages_count': unread,
            'unread_notifications_count': NotificationService.get_unread_count(user, scope=scope)}
