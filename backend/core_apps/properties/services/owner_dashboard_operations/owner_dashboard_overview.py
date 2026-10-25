"""OwnerDashboardOverview operations owned by OwnerDashboardService."""

from django.utils import timezone
from ...models import Property, PropertyVisit


class OwnerDashboardOverviewMixin:
    @classmethod
    def get_dashboard(cls, owner):
        """
        Builds the owner dashboard payload: profile header, summary stats and
        the list of pending visit requests awaiting the owner's response.
        """
        today = timezone.localdate()

        visits_this_week = PropertyVisit.objects.filter(
            property__owner=owner,
            created_at__date__gte=today - timezone.timedelta(days=6),
            created_at__date__lte=today,
        ).count()

        active_properties = Property.objects.filter(
            owner=owner, status=Property.Status.VERIFIED
        ).count()

        pending_requests = PropertyVisit.objects.filter(
            property__owner=owner, status=PropertyVisit.Status.PENDING
        ).count()

        pending_visits = (
            PropertyVisit.objects.filter(
                property__owner=owner, status=PropertyVisit.Status.PENDING
            )
            .select_related("property", "tenant", "tenant__profile")
            .order_by("-created_at")
        )

        return {
            "owner": owner,
            "visits_this_week": visits_this_week,
            "active_properties": active_properties,
            "overall_rating": 0.0,
            "pending_requests": pending_requests,
            "pending_visits": pending_visits,
        }
