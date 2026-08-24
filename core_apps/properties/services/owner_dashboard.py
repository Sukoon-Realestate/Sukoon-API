from django.db.models import Count, Q
from django.utils import timezone

from ..models import Property, PropertyVisit


class OwnerDashboardService:
    @staticmethod
    def get_dashboard(owner):
        """
        Builds the owner dashboard payload: profile header, summary stats and
        the list of pending visit requests awaiting the owner's response.
        """
        today = timezone.localdate()
        week_end = today + timezone.timedelta(days=7)

        visits_this_week = PropertyVisit.objects.filter(
            property__owner=owner,
            visit_date__gte=today,
            visit_date__lte=week_end,
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
            .order_by("visit_date", "visit_time")
        )

        return {
            "owner": owner,
            "visits_this_week": visits_this_week,
            "active_properties": active_properties,
            "overall_rating": 0.0,
            "pending_requests": pending_requests,
            "pending_visits": pending_visits,
        }
