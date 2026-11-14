"""Stable public imports for owner dashboard.

Implementation modules separate domain responsibilities without changing routes.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from core_apps.profiles.serializers import CloudinarySerializerField
from ..models import PropertyVisit

from .owner_dashboard_parts.owner_dashboard_pending_visit_serializer import (
    User,
    OwnerDashboardOwnerSerializer,
    OwnerDashboardPendingVisitSerializer,
    OwnerDashboardSerializer,
    OwnerPropertyRevenueSerializer,
    OwnerRevenueTransactionSerializer,
    OwnerRevenuesSerializer,
    OwnerProfileHeaderSerializer,
    OwnerProfileStatsSerializer,
    OwnerProfileAccountDetailsSerializer,
    OwnerPrivacyNoticeSerializer,
)
# Supported private imports stay outside the public star-import surface.
from .owner_dashboard_parts.owner_dashboard_pending_visit_serializer import (  # noqa: F401
    _ARABIC_WEEKDAYS,
    _ARABIC_MONTHS,
    _format_time_ar,
    _format_date_label,
)
from .owner_dashboard_parts.owner_profile_serializer import (
    OwnerRecentReviewSerializer,
    OwnerProfileSerializer,
)

# Preserve the existing public import surface, including compatibility seams.
__all__ = [
    'get_user_model',
    'serializers',
    'CloudinarySerializerField',
    'PropertyVisit',
    'User',
    'OwnerDashboardOwnerSerializer',
    'OwnerDashboardPendingVisitSerializer',
    'OwnerDashboardSerializer',
    'OwnerPropertyRevenueSerializer',
    'OwnerRevenueTransactionSerializer',
    'OwnerRevenuesSerializer',
    'OwnerProfileHeaderSerializer',
    'OwnerProfileStatsSerializer',
    'OwnerProfileAccountDetailsSerializer',
    'OwnerPrivacyNoticeSerializer',
    'OwnerRecentReviewSerializer',
    'OwnerProfileSerializer',
]
