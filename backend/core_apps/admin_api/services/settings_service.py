import logging
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)

# * In-memory platform settings store
_PLATFORM_SETTINGS = {
    "maxReviewHours": True,
    "tenantDocsRequired": False,
    "landlordDocsRequired": True,
    "autoVerification": True,
    "maxPhotosLimit": True,
    "reviewPeriodDays": False,
    "approxLocation": True,
    "hidePhoneDefault": True,
}


def get_platform_settings():
    """
    Returns current platform control settings and rules.
    """
    return _PLATFORM_SETTINGS


def update_platform_settings(payload):
    """
    Updates platform control settings and rules.
    """
    if not isinstance(payload, dict):
        raise ValidationError({"detail": "بيانات الإعدادات غير صالحة"})

    for key in _PLATFORM_SETTINGS.keys():
        if key in payload:
            _PLATFORM_SETTINGS[key] = bool(payload[key])

    return _PLATFORM_SETTINGS
