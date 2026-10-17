"""Explicit domain adapters. Source IDs never select an arbitrary import."""

from importlib import import_module
from rest_framework.exceptions import ValidationError

MODULES = {
    "tender": "housing_tenders.execution",
    "transition": "transition_network.execution",
    "company_scenario": "housing_scenarios.execution",
}
CAPABILITIES = {
    "tender": "collective_tender_execution",
    "transition": "housing_transition_execution",
    "company_scenario": "corporate_housing_execution",
}


def adapter(kind):
    if kind not in MODULES:
        raise ValidationError({"source_kind": "Unsupported execution source."})
    return import_module("core_apps.features.services." + MODULES[kind])
