"""Stable public imports for report serializers.

Implementation modules separate domain responsibilities without changing routes.
"""

from rest_framework import serializers
from core_apps.admin_api.models import UserReport

from .report_serializers_parts.support_ticket_serializer import (
    UserReportListSerializer,
    UserReportActionSerializer,
    SupportTicketSerializer,
)
from .report_serializers_parts.overview_ticket_serializer import (
    OverviewTicketSerializer,
)
