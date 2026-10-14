"""Stable public imports for property.

Implementation modules separate domain responsibilities without changing routes.
"""

import logging
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import (
    Avg,
    BooleanField,
    Count,
    Exists,
    FloatField,
    IntegerField,
    OuterRef,
    Subquery,
    Value,
)
from django.db.models.functions import Coalesce
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.response import Response
from core_apps.common.models import ContentView
from core_apps.common.idempotency import (
    execute_idempotent,
    request_key as get_idempotency_key,
    response_headers,
)
from core_apps.common.pagination import StandardResultsSetPagination
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.features.models import BoostCampaign
from ..filters import PropertyFilter
from ..models import (
    Property,
    PropertyFavorite,
    PropertyImage,
    PropertyType,
    PropertyVisit,
    SavedProperty,
)
from ..permissions import IsOwner, IsOwnerOrReadOnly
from ..serializers import (
    MyPropertyListSerializer,
    AvailablePlacesQuerySerializer,
    PropertyDetailSerializer,
    PropertyImageSerializer,
    PropertyImageUpdateSerializer,
    PropertyImageUploadSerializer,
    PropertyListSerializer,
    PropertyNewListSerializer,
    PropertySerializer,
    PropertyTypeSerializer,
    PropertyStatisticsSerializer,
    PropertyVisibilitySerializer,
)
from ..services import PropertyService

from .property_parts.property_filter_options_apiview import (
    logger,
    confirm_property_availability,
    get_client_ip,
    PropertyPagination,
    PropertyTypeListAPIView,
    PropertyFilterOptionsAPIView,
    AvailablePlacesAPIView,
)
from .property_parts.property_list_apiview import (
    PropertyListAPIView,
    PropertyNewListAPIView,
)
from .property_parts.property_detail_apiview import (
    PropertyCreateAPIView,
    PropertyDetailAPIView,
)
from .property_parts.my_property_list_apiview import (
    MyPropertyListAPIView,
    PropertyUpdateAPIView,
    PropertyDeleteAPIView,
)
from .property_parts.property_image_upload_apiview import (
    PropertyImageUploadAPIView,
    PropertyImageDetailAPIView,
    PropertyStatisticsAPIView,
    PropertyToggleVisibilityAPIView,
)
