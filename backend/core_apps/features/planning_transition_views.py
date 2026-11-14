"""Stable public imports for planning transition views.

Implementation modules separate domain responsibilities without changing routes.
"""

from django.db import transaction as transaction
from django.shortcuts import get_object_or_404 as get_object_or_404
from django.utils import timezone as timezone
from rest_framework.exceptions import (
    NotFound as NotFound,
    PermissionDenied as PermissionDenied,
    ValidationError as ValidationError,
)
from rest_framework.response import Response as Response
from .models import Lease as Lease, RentalInterest as RentalInterest
from .planning_models import TenancyTransition as TenancyTransition
from .planning_condition_views import participant_lease as participant_lease
from .services.planning import (
    check_revision as check_revision,
    civil_date as civil_date,
    display_name as display_name,
    mutate as mutate,
    page as page,
    planning_api as planning_api,
    require_planning as require_planning,
    selection_payload as selection_payload,
    text_field as text_field,
)
from .services.rental_phase2 import RentalConflict as RentalConflict

from .planning_transition_views_parts.transition_projection import (
    TERMINAL as TERMINAL,
    transition_actions as transition_actions,
    transition_projection as transition_projection,
    transition_payload as transition_payload,
    transition_for as transition_for,
    _candidates as _candidates,
    _nominate as _nominate,
)
from .planning_transition_views_parts.transition_detail_action import (
    _transition_list as _transition_list,
    move_out_notices as move_out_notices,
    replacement_requests as replacement_requests,
    transition_detail_action as transition_detail_action,
    MoveOutNoticesView as MoveOutNoticesView,
    ReplacementRequestsView as ReplacementRequestsView,
    TransitionDetailActionView as TransitionDetailActionView,
)
from .planning_transition_views_parts.reconcile_transitions import (
    replacement_candidates as replacement_candidates,
    candidate_invitation_payload as candidate_invitation_payload,
    replacement_invitations as replacement_invitations,
    replacement_candidate_consent as replacement_candidate_consent,
    reconcile_transitions as reconcile_transitions,
    ReplacementCandidateConsentView as ReplacementCandidateConsentView,
    ReplacementCandidatesView as ReplacementCandidatesView,
    ReplacementInvitationsView as ReplacementInvitationsView,
)

__all__ = [
    "Lease",
    "MoveOutNoticesView",
    "NotFound",
    "PermissionDenied",
    "RentalConflict",
    "RentalInterest",
    "ReplacementCandidateConsentView",
    "ReplacementCandidatesView",
    "ReplacementInvitationsView",
    "ReplacementRequestsView",
    "Response",
    "TERMINAL",
    "TenancyTransition",
    "TransitionDetailActionView",
    "ValidationError",
    "_candidates",
    "_nominate",
    "_transition_list",
    "candidate_invitation_payload",
    "check_revision",
    "civil_date",
    "display_name",
    "get_object_or_404",
    "move_out_notices",
    "mutate",
    "page",
    "participant_lease",
    "planning_api",
    "reconcile_transitions",
    "replacement_candidate_consent",
    "replacement_candidates",
    "replacement_invitations",
    "replacement_requests",
    "require_planning",
    "selection_payload",
    "text_field",
    "timezone",
    "transaction",
    "transition_actions",
    "transition_detail_action",
    "transition_for",
    "transition_payload",
    "transition_projection",
]
