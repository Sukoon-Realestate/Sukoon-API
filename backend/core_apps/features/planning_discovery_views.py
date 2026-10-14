"""Stable public imports for planning discovery views.

Implementation modules separate domain responsibilities without changing routes.
"""

import math
import re
from itertools import islice
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.conf import settings
from django.db import transaction
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_time
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from core_apps.properties.models import City
from .planning_models import CommuteSearch, TenantAssistantTurn
from .providers import fake_provider_available
from .services.planning_providers import (
    mock_discovery,
    extract_criteria,
    provider_budget,
)
from .services.commute_jobs import destination_constraints
from .services.commands import command_identity
from .services.rental_phase2 import replay_operation, fingerprint
from .services.planning import (
    money,
    mutate,
    offer_money,
    page,
    planning_api,
    public_properties,
    text_field,
)
from .services.rental_phase2 import RentalConflict
from .services.tenancy_invitations import resolve_offer_snapshot

from .planning_discovery_views_parts.catalog_matches import (
    catalog_matches,
    commute_payload,
)
from .planning_discovery_views_parts.mock_duration import (
    _mock_duration,
)
from .planning_discovery_views_parts.commute_searches import (
    commute_searches,
    _commute,
    commute_detail,
)
from .planning_discovery_views_parts.commute_results import (
    commute_cancel,
    commute_results,
)
from .planning_discovery_views_parts.tenant_assistant_turns import (
    tenant_assistant_turns,
)
