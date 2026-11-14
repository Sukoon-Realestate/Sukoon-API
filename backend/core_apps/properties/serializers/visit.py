"""Stable public imports for visit.

Implementation modules separate domain responsibilities without changing routes.
"""

from datetime import date, datetime
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _  # noqa: F401 - private compatibility import
from rest_framework import serializers
from core_apps.profiles.serializers import CloudinarySerializerField
from core_apps.properties.serializers.property import PropertyListSerializer
from ..phone_disclosure import counterpart_phone_payload
from ..models import Property, PropertyVisit, PropertyVisitReview
from ..services import PropertyVisitService

from .visit_parts.property_visit_serializer import (
    get_visit_language,
    User,
    PostVisitContextMixin,
    PropertyVisitSerializer,
)
# Supported private imports stay outside the public star-import surface.
from .visit_parts.property_visit_serializer import (  # noqa: F401
    _ARABIC_WEEKDAYS,
    _ENGLISH_WEEKDAYS,
    _ARABIC_MONTHS,
    _ENGLISH_MONTHS,
    _ARABIC_VISIT_STATUS,
    _ENGLISH_VISIT_STATUS,
    _ARABIC_REQUEST_STATUS,
    _ENGLISH_REQUEST_STATUS,
)
from .visit_parts.tenant_visit_list_serializer import (
    TenantVisitListSerializer,
    VisitTenantSerializer,
    PropertyVisitDetailSerializer,
)
from .visit_parts.visit_request_input_serializer import (
    PropertyVisitCreateSerializer,
    PropertyVisitUpdateSerializer,
)
from .visit_parts.visit_owner_serializer import (
    VisitPropertySummarySerializer,
    VisitOwnerSerializer,
    PropertyVisitReviewSerializer,
    PropertyReviewItemSerializer,
)
from .visit_parts.tenant_visit_request_serializer import (
    TenantVisitRequestSerializer,
    TenantVisitRequestDetailSerializer,
)
# Supported private imports stay outside the public star-import surface.
from .visit_parts.tenant_visit_request_serializer import (  # noqa: F401
    _format_time_compact,
    _format_time_clock,
    _format_owner_schedule_label,
    _format_full_date,
    _format_time_ar_compact,
    _format_time_ar_clock,
    _format_full_date_ar,
)
from .visit_parts.owner_visit_request_card_serializer import (
    OwnerVisitRequestCardSerializer,
)
# Supported private imports stay outside the public star-import surface.
from .visit_parts.owner_visit_request_card_serializer import (  # noqa: F401
    _OWNER_CARD_STATUS_LABEL_AR,
    _OWNER_CARD_STATUS_LABEL_EN,
    _OWNER_CARD_STATUS_LABEL,
    _OWNER_DETAIL_STATUS_LABEL_AR,
    _OWNER_DETAIL_STATUS_LABEL_EN,
    _OWNER_DETAIL_STATUS_LABEL,
)
from .visit_parts.owner_visit_request_detail_serializer import (
    OwnerVisitRequestDetailSerializer,
    OwnerVisitRejectSerializer,
)

# Preserve the existing public import surface, including compatibility seams.
__all__ = [
    'date',
    'datetime',
    'get_user_model',
    'timezone',
    'serializers',
    'CloudinarySerializerField',
    'PropertyListSerializer',
    'counterpart_phone_payload',
    'Property',
    'PropertyVisit',
    'PropertyVisitReview',
    'PropertyVisitService',
    'get_visit_language',
    'User',
    'PostVisitContextMixin',
    'PropertyVisitSerializer',
    'TenantVisitListSerializer',
    'VisitTenantSerializer',
    'PropertyVisitDetailSerializer',
    'PropertyVisitCreateSerializer',
    'PropertyVisitUpdateSerializer',
    'VisitPropertySummarySerializer',
    'VisitOwnerSerializer',
    'PropertyVisitReviewSerializer',
    'PropertyReviewItemSerializer',
    'TenantVisitRequestSerializer',
    'TenantVisitRequestDetailSerializer',
    'OwnerVisitRequestCardSerializer',
    'OwnerVisitRequestDetailSerializer',
    'OwnerVisitRejectSerializer',
]
