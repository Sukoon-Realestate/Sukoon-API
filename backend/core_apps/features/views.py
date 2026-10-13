"""Stable public imports for views.

Implementation modules separate domain responsibilities without changing routes.
"""

from .catalog_models import PromotionOption
import copy
import hashlib
import json
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import (
    APIException,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from core_apps.common.models import ContentView
from core_apps.properties.models import Property, PropertyVisit, SavedProperty
from .models import (
    BoostCampaign,
    CheckoutSession,
    IdempotencyRecord,
    Lease,
    ListingSuggestion,
    RentInvoice,
    SearchAlert,
    TenancyInvitation,
)
from .pagination import FeaturePagination
from .renderers import FeatureJsonRenderer
from .serializers import (
    AlertCreateSerializer,
    BoostCampaignSerializer,
    LeaseCreateSerializer,
    LeaseSerializer,
    RentInvoiceSerializer,
    RevisionRequestSerializer,
    SearchAlertSerializer,
    TenancyInvitationCreateSerializer,
    TenancyInvitationResponseSerializer,
    TenancyInvitationSerializer,
)
from .services.tenancy_invitations import (
    InvitationConflict,
    LIVE_LEASE_STATUSES,
    create_notification_for_invitation,
    create_notification_for_response,
    invitation_is_eligible,
    localized,
    refresh_effective_status,
    resolve_offer_snapshot,
    validate_accounts,
)
from .services.rental_foundation import (
    capabilities_for,
    get_authorized_rental_subject,
    private_no_store,
)
from .services.lease_permissions import can_cancel_draft

from .views_parts.rental_operation_lookup import (
    User,
    FEATURE_DECORATORS,
    LEASE_TEMPLATES,
    Conflict,
    _fingerprint,
    _replay,
    _remember,
    rental_capabilities,
    rental_operation_lookup,
    _paginate,
)
from .views_parts.planning_capabilities import (
    configuration,
    planning_capabilities,
)
from .views_parts.boost_campaigns import (
    boost_campaigns,
    search_alerts,
    search_alert_detail,
)
from .views_parts.listing_suggestions import (
    owner_analytics,
    listing_suggestions,
)
from .views_parts.lease_configuration import (
    lease_configuration,
    lease_tenants,
)
from .views_parts.tenancy_invitations import (
    tenancy_invitations,
)
from .views_parts.tenancy_invitation_respond import (
    _participant_invitation,
    tenancy_invitation_detail,
    tenancy_invitation_respond,
    _lease_queryset,
)
from .views_parts.leases import (
    leases,
    _get_authorized_lease,
    lease_detail,
)
from .views_parts.lease_cancel import (
    lease_signing_session,
    lease_cancel,
    _invoice_queryset,
    rent_invoices,
    _get_authorized_invoice,
    rent_invoice_detail,
)
from .views_parts.rent_invoice_checkout import (
    rent_invoice_checkout,
)
