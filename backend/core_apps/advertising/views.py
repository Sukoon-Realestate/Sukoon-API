"""Stable public imports for views.

Implementation modules separate domain responsibilities without changing routes.
"""

from django.core.paginator import EmptyPage, Paginator
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from datetime import timezone as datetime_timezone
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from .models import Advertisement, AdvertisementOperation, AdvertisingPlan
from .renderers import AdvertisingJsonRenderer
from .serializers import AdvertisementCreateSerializer, MockPaymentSerializer
from .services import (
    AdvertisingServiceError,
    activate_with_mock_payment,
    create_advertisement,
    ensure_media_persisted,
    is_publicly_eligible,
    media_is_available,
    effective_status,
    plan_payload,
    record_rejected_operation,
)

from .views_parts.language import (
    MESSAGES,
    ERROR_MESSAGES_AR,
    language,
    message,
    envelope,
    error_response,
    validation_error_response,
    finalize,
    iso8601,
)
from .views_parts.owner_advertisement_collection import (
    banner_url,
    payment_payload,
    advertisement_payload,
    plan_list,
    owner_advertisement_collection,
    owner_advertisement_detail,
)
from .views_parts.tenant_home_placement import (
    mock_payment,
    operation_detail,
    tenant_home_placement,
    advertisement_media,
)
