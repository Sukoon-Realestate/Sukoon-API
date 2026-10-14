"""Stable public imports for planning transition views.

Implementation modules separate domain responsibilities without changing routes.
"""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from .models import Lease, RentalInterest
from .planning_models import TenancyTransition
from .planning_condition_views import participant_lease
from .services.planning import (
    check_revision,
    civil_date,
    display_name,
    mutate,
    page,
    planning_api,
    require_planning,
    selection_payload,
    text_field,
)
from .services.rental_phase2 import RentalConflict

from .planning_transition_views_parts.transition_projection import (
    TERMINAL,
    transition_actions,
    transition_projection,
    transition_payload,
    transition_for,
    _candidates,
    _nominate,
)
from .planning_transition_views_parts.transition_detail_action import (
    _transition_list,
    move_out_notices,
    replacement_requests,
    transition_detail_action,
)
from .planning_transition_views_parts.reconcile_transitions import (
    replacement_candidates,
    candidate_invitation_payload,
    replacement_invitations,
    replacement_candidate_consent,
    reconcile_transitions,
)
