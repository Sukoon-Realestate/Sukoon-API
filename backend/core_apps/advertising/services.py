"""Stable public imports for services.

Implementation modules separate domain responsibilities without changing routes.
"""

import calendar
import hashlib
import json
import warnings
from datetime import datetime, timedelta, timezone as datetime_timezone
from io import BytesIO
from zoneinfo import ZoneInfo
from django.db import IntegrityError, transaction
from django.utils import timezone
from PIL import Image, UnidentifiedImageError
from core_apps.properties.models import Property
from .models import (
    Advertisement,
    AdvertisementMedia,
    AdvertisementOperation,
    AdvertisingPlan,
    MockAdvertisementPayment,
)

from .services_parts.validate_banner import (
    CAIRO,
    MAX_BANNER_BYTES,
    ALLOWED_IMAGE_FORMATS,
    AdvertisingServiceError,
    translated_plan_title,
    plan_payload,
    validate_banner,
    property_is_publishable,
    eligible_offer,
    validate_destination,
    payload_fingerprint,
)
from .services_parts.create_advertisement import (
    create_advertisement,
    record_rejected_operation,
)
# Supported private imports stay outside the public star-import surface.
from .services_parts.create_advertisement import (  # noqa: F401
    _valid_local_datetime,
)
from .services_parts.ensure_media_persisted import (
    resolve_cairo_local,
    calendar_expiry,
    effective_status,
    destination_is_eligible,
    ensure_media_persisted,
    media_is_available,
)
from .services_parts.activate_with_mock_payment import (
    activate_with_mock_payment,
    is_publicly_eligible,
)

# Preserve the existing public import surface, including compatibility seams.
__all__ = [
    'calendar',
    'hashlib',
    'json',
    'warnings',
    'datetime',
    'timedelta',
    'datetime_timezone',
    'BytesIO',
    'ZoneInfo',
    'IntegrityError',
    'transaction',
    'timezone',
    'Image',
    'UnidentifiedImageError',
    'Property',
    'Advertisement',
    'AdvertisementMedia',
    'AdvertisementOperation',
    'AdvertisingPlan',
    'MockAdvertisementPayment',
    'CAIRO',
    'MAX_BANNER_BYTES',
    'ALLOWED_IMAGE_FORMATS',
    'AdvertisingServiceError',
    'translated_plan_title',
    'plan_payload',
    'validate_banner',
    'property_is_publishable',
    'eligible_offer',
    'validate_destination',
    'payload_fingerprint',
    'create_advertisement',
    'record_rejected_operation',
    'resolve_cairo_local',
    'calendar_expiry',
    'effective_status',
    'destination_is_eligible',
    'ensure_media_persisted',
    'media_is_available',
    'activate_with_mock_payment',
    'is_publicly_eligible',
]
