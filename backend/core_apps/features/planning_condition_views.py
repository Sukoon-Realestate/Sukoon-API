"""Stable public imports for planning condition views.

Implementation modules separate domain responsibilities without changing routes.
"""

import re
from copy import deepcopy
import uuid
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from .models import Lease, PrivateAccessRevocation, RentalEvidence
from .planning_models import ConditionReport
from .rental_phase4_views import evidence_payload
from .services.planning import (
    check_revision,
    civil_date,
    display_name,
    mutate,
    page,
    planning_api,
    selection_payload,
    text_field,
)
from .services.rental_phase2 import RentalConflict

from .planning_condition_views_parts.condition_report_context import (
    participant_lease,
    report_actions,
    report_payload,
    report_for,
    baseline_for,
    lease_selection,
    condition_report_context,
    _acknowledgement,
)
from .planning_condition_views_parts.report_snapshot import (
    report_snapshot,
    _report_values,
)
from .planning_condition_views_parts.condition_report_action import (
    condition_reports,
    condition_report_detail,
    condition_report_action,
)
