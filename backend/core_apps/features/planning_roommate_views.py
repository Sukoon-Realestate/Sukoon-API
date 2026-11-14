"""Stable public imports for planning roommate views.

Implementation modules separate domain responsibilities without changing routes.
"""

from django.db import IntegrityError as IntegrityError, transaction as transaction
from django.db.models import Q as Q
from django.shortcuts import get_object_or_404 as get_object_or_404
from rest_framework.exceptions import (
    NotFound as NotFound,
    PermissionDenied as PermissionDenied,
    ValidationError as ValidationError,
)
from rest_framework.response import Response as Response
from .planning_models import (
    LifestyleProfile as LifestyleProfile,
    RoommateConnection as RoommateConnection,
)
from .services.planning import (
    check_revision as check_revision,
    display_name as display_name,
    mutate as mutate,
    page as page,
    planning_api as planning_api,
    text_field as text_field,
    criteria_payload as criteria_payload,
)
from .services.rental_phase2 import RentalConflict as RentalConflict
from .services.lifestyle_matching import (
    profile_extensions as profile_extensions,
    match_facts as match_facts,
    disclosure_scope as disclosure_scope,
)

from .planning_roommate_views_parts.profile_values import (
    DIMENSIONS as DIMENSIONS,
    lifestyle_payload as lifestyle_payload,
    profile_values as profile_values,
    lifestyle_profile as lifestyle_profile,
    connections as connections,
    roommate_actions as roommate_actions,
    disclosures as disclosures,
    candidate_payload as candidate_payload,
    LifestyleProfileView as LifestyleProfileView,
)
from .planning_roommate_views_parts.roommate_candidate_action import (
    connection_payload as connection_payload,
    roommate_candidates as roommate_candidates,
    roommate_connections as roommate_connections,
    roommate_candidate_action as roommate_candidate_action,
    RoommateCandidateActionView as RoommateCandidateActionView,
    RoommateCandidatesView as RoommateCandidatesView,
    RoommateConnectionsView as RoommateConnectionsView,
)
from .planning_roommate_views_parts.roommate_connection_action import (
    roommate_connection_action as roommate_connection_action,
    RoommateConnectionActionView as RoommateConnectionActionView,
)

__all__ = [
    "DIMENSIONS",
    "IntegrityError",
    "LifestyleProfile",
    "LifestyleProfileView",
    "NotFound",
    "PermissionDenied",
    "Q",
    "RentalConflict",
    "Response",
    "RoommateCandidateActionView",
    "RoommateCandidatesView",
    "RoommateConnection",
    "RoommateConnectionActionView",
    "RoommateConnectionsView",
    "ValidationError",
    "candidate_payload",
    "check_revision",
    "connection_payload",
    "connections",
    "criteria_payload",
    "disclosure_scope",
    "disclosures",
    "display_name",
    "get_object_or_404",
    "lifestyle_payload",
    "lifestyle_profile",
    "match_facts",
    "mutate",
    "page",
    "planning_api",
    "profile_extensions",
    "profile_values",
    "roommate_actions",
    "roommate_candidate_action",
    "roommate_candidates",
    "roommate_connection_action",
    "roommate_connections",
    "text_field",
    "transaction",
]
