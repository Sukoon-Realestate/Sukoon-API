"""Stable public imports for planning roommate views.

Implementation modules separate domain responsibilities without changing routes.
"""

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from .planning_models import LifestyleProfile, RoommateConnection
from .services.planning import (
    check_revision,
    display_name,
    mutate,
    page,
    planning_api,
    text_field,
    criteria_payload,
)
from .services.rental_phase2 import RentalConflict
from .services.lifestyle_matching import (
    profile_extensions,
    match_facts,
    disclosure_scope,
)

from .planning_roommate_views_parts.profile_values import (
    DIMENSIONS,
    lifestyle_payload,
    profile_values,
    lifestyle_profile,
    connections,
    roommate_actions,
    disclosures,
    candidate_payload,
)
from .planning_roommate_views_parts.roommate_candidate_action import (
    connection_payload,
    roommate_candidates,
    roommate_connections,
    roommate_candidate_action,
)
from .planning_roommate_views_parts.roommate_connection_action import (
    roommate_connection_action,
)
