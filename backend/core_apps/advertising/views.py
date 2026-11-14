"""Stable public imports for views.

Implementation modules separate domain responsibilities without changing routes.
"""

from django.core.paginator import EmptyPage as EmptyPage, Paginator as Paginator
from django.db import transaction as transaction
from django.http import FileResponse as FileResponse
from django.shortcuts import get_object_or_404 as get_object_or_404
from django.urls import reverse as reverse
from django.utils import timezone as timezone
from rest_framework import permissions as permissions, status as status
from rest_framework.decorators import (
    api_view as api_view,
    parser_classes as parser_classes,
    permission_classes as permission_classes,
    renderer_classes as renderer_classes,
)
from rest_framework.parsers import (
    FormParser as FormParser,
    JSONParser as JSONParser,
    MultiPartParser as MultiPartParser,
)
from rest_framework.response import Response as Response
from .models import (
    Advertisement as Advertisement,
    AdvertisementOperation as AdvertisementOperation,
    AdvertisingPlan as AdvertisingPlan,
)
from .renderers import AdvertisingJsonRenderer as AdvertisingJsonRenderer
from .serializers import (
    AdvertisementCreateSerializer as AdvertisementCreateSerializer,
    MockPaymentSerializer as MockPaymentSerializer,
)
from .services import (
    AdvertisingServiceError as AdvertisingServiceError,
    activate_with_mock_payment as activate_with_mock_payment,
    create_advertisement as create_advertisement,
    ensure_media_persisted as ensure_media_persisted,
    is_publicly_eligible as is_publicly_eligible,
    media_is_available as media_is_available,
    effective_status as effective_status,
    plan_payload as plan_payload,
    record_rejected_operation as record_rejected_operation,
)

from .views_parts.language import (
    MESSAGES as MESSAGES,
    ERROR_MESSAGES_AR as ERROR_MESSAGES_AR,
    language as language,
    message as message,
    envelope as envelope,
    error_response as error_response,
    validation_error_response as validation_error_response,
    finalize as finalize,
    iso8601 as iso8601,
)
from .views_parts.owner_advertisement_collection import (
    banner_url as banner_url,
    payment_payload as payment_payload,
    advertisement_payload as advertisement_payload,
    plan_list as plan_list,
    owner_advertisement_collection as owner_advertisement_collection,
    owner_advertisement_detail as owner_advertisement_detail,
    OwnerAdvertisementCollectionView as OwnerAdvertisementCollectionView,
    OwnerAdvertisementDetailView as OwnerAdvertisementDetailView,
    PlanListView as PlanListView,
)
from .views_parts.tenant_home_placement import (
    mock_payment as mock_payment,
    operation_detail as operation_detail,
    tenant_home_placement as tenant_home_placement,
    advertisement_media as advertisement_media,
    AdvertisementMediaView as AdvertisementMediaView,
    MockPaymentView as MockPaymentView,
    OperationDetailView as OperationDetailView,
    TenantHomePlacementView as TenantHomePlacementView,
)

__all__ = [
    "Advertisement",
    "AdvertisementCreateSerializer",
    "AdvertisementMediaView",
    "AdvertisementOperation",
    "AdvertisingJsonRenderer",
    "AdvertisingPlan",
    "AdvertisingServiceError",
    "ERROR_MESSAGES_AR",
    "EmptyPage",
    "FileResponse",
    "FormParser",
    "JSONParser",
    "MESSAGES",
    "MockPaymentSerializer",
    "MockPaymentView",
    "MultiPartParser",
    "OperationDetailView",
    "OwnerAdvertisementCollectionView",
    "OwnerAdvertisementDetailView",
    "Paginator",
    "PlanListView",
    "Response",
    "TenantHomePlacementView",
    "activate_with_mock_payment",
    "advertisement_media",
    "advertisement_payload",
    "api_view",
    "banner_url",
    "create_advertisement",
    "effective_status",
    "ensure_media_persisted",
    "envelope",
    "error_response",
    "finalize",
    "get_object_or_404",
    "is_publicly_eligible",
    "iso8601",
    "language",
    "media_is_available",
    "message",
    "mock_payment",
    "operation_detail",
    "owner_advertisement_collection",
    "owner_advertisement_detail",
    "parser_classes",
    "payment_payload",
    "permission_classes",
    "permissions",
    "plan_list",
    "plan_payload",
    "record_rejected_operation",
    "renderer_classes",
    "reverse",
    "status",
    "tenant_home_placement",
    "timezone",
    "transaction",
    "validation_error_response",
]
