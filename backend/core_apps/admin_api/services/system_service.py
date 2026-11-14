"""Stable public imports for system service.

Implementation modules separate domain responsibilities without changing routes.
"""

import logging
from datetime import datetime
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.admin_api.models import KYCSubmission, StaffProfile
from core_apps.properties.models import Property
from core_apps.admin_api.models import UserReport

from .system_service_parts.logger import (
    logger,
)
# Supported private imports stay outside the public star-import surface.
from .system_service_parts.logger import (  # noqa: F401
    _PUSH_CAMPAIGNS,
)
from .system_service_parts.get_audit_logs import (
    get_audit_logs,
)
from .system_service_parts.get_system_health import (
    get_system_health,
    get_push_campaigns,
    send_push_notification,
)

# Preserve the existing public import surface, including compatibility seams.
__all__ = [
    'logging',
    'datetime',
    'timezone',
    'ValidationError',
    'KYCSubmission',
    'StaffProfile',
    'Property',
    'UserReport',
    'logger',
    'get_audit_logs',
    'get_system_health',
    'get_push_campaigns',
    'send_push_notification',
]
