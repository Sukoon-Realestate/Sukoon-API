"""Stable public imports for rental phase5 views.

Implementation modules separate domain responsibilities without changing routes.
"""

from datetime import time, timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from .models import (
    ChangeSigningSession,
    Lease,
    MaintenanceEvent,
    MaintenanceRequest,
    RentalChange,
    RentalEvidence,
    RentInvoice,
)
from .providers import (
    mock_completion_metadata,
    get_rental_provider,
    require_rental_provider,
)
from .renderers import FeatureJsonRenderer
from .services.cycle_permissions import MAINTENANCE_TRANSITIONS, cycle_actions
from .services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .services.rental_phase3 import cairo_instant

from .rental_phase5_views_parts.maintenance_payload import (
    MAINTENANCE_ACTIONS,
    _money,
    _lease,
    _safe_evidence,
    maintenance_payload,
    _maintenance,
)
from .rental_phase5_views_parts.maintenance_requests import (
    maintenance_requests,
    maintenance_detail,
)
from .rental_phase5_views_parts.maintenance_action import (
    maintenance_action,
    change_payload,
    _change,
)
from .rental_phase5_views_parts.change_collection import (
    change_collection,
)
from .rental_phase5_views_parts.change_respond import (
    payment_extensions,
    amendments,
    renewals,
    terminations,
    external_claims,
    external_claim_create,
    change_detail,
    change_respond,
)
from .rental_phase5_views_parts.change_signing_session import (
    submit_change_for_signature,
    change_signing_session,
    complete_change_signature,
)
