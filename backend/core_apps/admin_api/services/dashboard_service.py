"""Stable public imports for dashboard service.

Implementation modules separate domain responsibilities without changing routes.
"""

import logging
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from core_apps.properties.models import Property
from core_apps.admin_api.models import KYCSubmission, UserReport
from core_apps.properties.models.visit import PropertyVisit

from .dashboard_service_parts.get_executive_dashboard_stats import (
    logger,
    User,
    get_executive_dashboard_stats,
    _format_time_ago,
)
from .dashboard_service_parts.get_dashboard_overview_stats import (
    get_dashboard_overview_stats,
)
