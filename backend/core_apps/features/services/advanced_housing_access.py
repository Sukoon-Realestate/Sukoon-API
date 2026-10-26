"""Registration only; each domain retains its own current permission policy."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework.exceptions import NotFound, PermissionDenied
from .housing_tenders import access as tenders
from .living_lab import access as labs
from .housing_scenarios import access as scenarios
from .transition_network import access as transitions

DOMAINS = (tenders, labs, scenarios, transitions)
CAPABILITIES = {
    "collective_tender_planning": tenders,
    "shared_living_lab": labs,
    "corporate_housing_simulation": scenarios,
    "housing_transition_planning": transitions,
}


def subject(user, identifier):
    from .advanced_execution.plans import subject as execution_subject

    execution = execution_subject(user, identifier)
    if execution is not None:
        return execution
    for domain in DOMAINS:
        item = domain.subject(user, identifier)
        if item is not None:
            return item
    return None


def actions(user, capability, subject_id=""):
    from .advanced_execution.plans import actions as execution_actions
    from ..advanced_execution_models import AdvancedExecution

    try:
        if subject_id and AdvancedExecution.objects.filter(id=subject_id).exists():
            return execution_actions(user, capability, subject_id)
    except (NotFound, Http404, PermissionDenied, DjangoValidationError, ValueError):
        return []
    if capability in {
        "housing_transition_execution",
        "collective_tender_execution",
        "conditional_group_execution",
        "corporate_housing_execution",
    }:
        domain = {
            "housing_transition_execution": transitions,
            "collective_tender_execution": tenders,
            "conditional_group_execution": tenders,
            "corporate_housing_execution": scenarios,
        }[capability]
    else:
        domain = CAPABILITIES.get(capability)
    if domain is None:
        return []
    try:
        return domain.actions(user, capability, subject_id)
    except (NotFound, Http404, PermissionDenied, DjangoValidationError, ValueError):
        return []
