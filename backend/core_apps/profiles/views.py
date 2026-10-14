"""Stable public imports for views.

Implementation modules separate domain responsibilities without changing routes.
"""

import logging
from typing import List
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from core_apps.common.pagination import (
    ClientResultsSetPagination,
    StandardResultsSetPagination,
)
from core_apps.common.renderers import GenericJsonRenderer
from .models import Contract, Profile, UserSettings
from .serializers import (
    AccountSummaryScreenSerializer,
    MyAccountScreenSerializer,
    OwnerUnreadCountsSerializer,
    ProfileEditSerializer,
    ProfileSerializer,
    TenantContractSerializer,
    TenantMyRateSerializer,
    TenantUnreadCountsSerializer,
    UpdateProfileSerializer,
    UserSettingsSerializer,
    VerificationStatusSerializer,
)
from .services import ProfileService
from core_apps.properties.models import PropertyVisitReview

from .views_parts.profile_edit_apiview import (
    logger,
    User,
    ProfileListAPIView,
    ProfileDetailAPIView,
    ProfileUpdateAPIView,
    MyAccountDetailAPIView,
    AccountSummaryDetailAPIView,
    ProfileEditAPIView,
)
from .views_parts.user_settings_apiview import (
    UserSettingsAPIView,
    OwnerUnreadCountsAPIView,
    TenantUnreadCountsAPIView,
    TenantMyRatesListAPIView,
    VerificationStatusAPIView,
    TenantContractsListAPIView,
)
