from django.db.models import Count, Q
from django.utils import timezone

from ..models import Property, PropertyVisit, PropertyVisitReview


from .owner_dashboard_operations.owner_dashboard_overview import (
    OwnerDashboardOverviewMixin,
)
from .owner_dashboard_operations.owner_revenue import OwnerRevenueMixin
from .owner_dashboard_operations.owner_profile import OwnerProfileMixin


class OwnerDashboardService(
    OwnerDashboardOverviewMixin, OwnerRevenueMixin, OwnerProfileMixin
):
    """Public service dispatch with domain-specific responsibilities."""
