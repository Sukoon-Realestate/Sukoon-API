"""Stable public imports for planning.

Implementation modules separate domain responsibilities without changing routes.
"""

from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from config.planning import SERVICES
from core_apps.properties.models import City, Property
from core_apps.users.models import User
from ..pagination import FeaturePagination
from ..renderers import FeatureJsonRenderer
from .commands import command_identity, money_minor
from .rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .tenancy_invitations import resolve_offer_snapshot

from .planning_parts.selection_payload import (
    enabled_services,
    require_planning,
    page,
    check_revision,
    mutate,
    display_name,
    text_field,
    civil_date,
    public_properties,
    eligible_owner,
    selection_payload,
)
from .planning_parts.criteria import (
    selection,
    offer_money,
    money,
    criteria,
)
from .planning_parts.validate_payload_types import (
    criteria_payload,
    purge_expired_discovery,
    validate_payload_types,
    planning_api,
)
