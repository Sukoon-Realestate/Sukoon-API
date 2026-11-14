"""Stable public imports for property service.

Implementation modules separate domain responsibilities without changing routes.
"""

import uuid
import logging
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from core_apps.properties.models import (
    Property,
    PropertyImage,
    PropertyType,
    PropertyVisit,
)
from core_apps.common.models import ContentView
from core_apps.admin_api.models import UserReport

from .property_service_parts.get_admin_properties_queryset import (
    logger,
    User,
    get_admin_properties_queryset,
    get_admin_property_metrics,
)
# Supported private imports stay outside the public star-import surface.
from .property_service_parts.get_admin_properties_queryset import (  # noqa: F401
    _get_property_by_identifier,
)
from .property_service_parts.get_admin_property_detail import (
    get_admin_property_detail,
    approve_admin_property,
    reject_admin_property,
    request_admin_property_revision,
)

# Preserve the existing public import surface, including compatibility seams.
__all__ = [
    'uuid',
    'logging',
    'ContentType',
    'get_user_model',
    'Count',
    'Q',
    'Avg',
    'get_object_or_404',
    'timezone',
    'NotFound',
    'ValidationError',
    'Property',
    'PropertyImage',
    'PropertyType',
    'PropertyVisit',
    'ContentView',
    'UserReport',
    'logger',
    'User',
    'get_admin_properties_queryset',
    'get_admin_property_metrics',
    'get_admin_property_detail',
    'approve_admin_property',
    'reject_admin_property',
    'request_admin_property_revision',
]
