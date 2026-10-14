"""Stable public imports for visit.

Implementation modules separate domain responsibilities without changing routes.
"""

import logging
from datetime import timedelta
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from core_apps.common.idempotency import (
    execute_idempotent,
    request_key as get_idempotency_key,
    response_headers,
)
from core_apps.common.pagination import StandardResultsSetPagination
from core_apps.common.renderers import GenericJsonRenderer
from ..filters import PropertyVisitFilter
from ..models import Property, PropertyVisit, PropertyVisitReview
from ..permissions import IsTenantOrPropertyOwner
from ..serializers import (
    AvailableDatesQuerySerializer,
    OwnerAvailabilityWeekQuerySerializer,
    OwnerAvailabilityDayUpdateSerializer,
    OwnerVisitCalendarQuerySerializer,
    OwnerVisitRequestCardSerializer,
    OwnerVisitRequestDetailSerializer,
    OwnerVisitRejectSerializer,
    PropertyVisitCreateSerializer,
    PropertyVisitDetailSerializer,
    PropertyVisitSerializer,
    PropertyVisitUpdateSerializer,
    TenantVisitListSerializer,
    PropertyVisitReviewSerializer,
    PropertyReviewItemSerializer,
    TenantVisitRequestDetailSerializer,
    TenantVisitRequestSerializer,
)
from ..serializers.visit import get_visit_language
from ..services import PropertyVisitService

from .visit_parts.property_visit_create_apiview import (
    logger,
    PropertyVisitPagination,
    PropertyVisitCreateAPIView,
    PropertyAvailableDatesAPIView,
    OwnerAvailabilityWeekAPIView,
    OwnerVisitCalendarAPIView,
)
from .visit_parts.owner_property_visit_list_apiview import (
    TenantPropertyVisitListAPIView,
    OwnerPropertyVisitListAPIView,
    PropertyVisitDetailAPIView,
    PropertyVisitUpdateAPIView,
    TenantVisitRequestListAPIView,
    TenantVisitRequestDetailAPIView,
)
from .visit_parts.property_visit_review_create_apiview import (
    PropertyVisitCancelAPIView,
    PropertyVisitReviewCreateAPIView,
    PropertyReviewPagination,
)
from .visit_parts.property_review_list_apiview import (
    PropertyReviewListAPIView,
    OwnerVisitRequestPagination,
    OwnerVisitRequestListAPIView,
    OwnerVisitRequestDetailAPIView,
)
from .visit_parts.owner_visit_request_reject_apiview import (
    OwnerVisitRequestRejectAPIView,
    OwnerVisitRequestAcceptAPIView,
)
