"""Versioned, opt-in policies for the advanced planning releases.

Deployment selection never grants resource authority or enables an unsupported
provider/contract workflow. Disable creation without removing private history.
"""

from django.core.exceptions import ImproperlyConfigured

POLICY_VERSION = "advanced-housing-v2"
PLANNING_SERVICES = (
    "collective_tender_planning",
    "shared_living_lab",
    "corporate_housing_simulation",
    "asset_passport",
    "housing_transition_planning",
)
PROVIDER_SERVICES = (
    "collective_tender_execution",
    "conditional_group_execution",
    "corporate_housing_execution",
    "asset_assisted_analysis",
    "housing_transition_execution",
)
SERVICES = PLANNING_SERVICES + PROVIDER_SERVICES
# Kept as a compatibility export for older settings/tests importing the catalog.
# Runtime readiness, rather than this catalog, now gates provider-backed actions.
UNAVAILABLE_SERVICES = ()


def mock_mode_available():
    from django.conf import settings
    from core_apps.features.providers import fake_provider_available

    return (
        getattr(settings, "ADVANCED_HOUSING_PROVIDER_MODE", "disabled") == "mock"
        and fake_provider_available()
    )


def require_mock_mode():
    from rest_framework.exceptions import PermissionDenied

    if not mock_mode_available():
        raise PermissionDenied(
            {
                "code": "capability_unavailable",
                "message": "Enable the explicitly configured mock provider to continue.",
            }
        )


def manual_review_available():
    from django.conf import settings

    return getattr(settings, "ADVANCED_HOUSING_PROVIDER_MODE", "disabled") == "manual"


def provider_configuration():
    available = mock_mode_available()
    manual = manual_review_available()
    return {
        "policy_version": POLICY_VERSION,
        "provider_mode": "mock" if available else "disabled",
        "simulated": available,
        "planning_only": not available,
        **{service: available for service in PROVIDER_SERVICES},
        "asset_assisted_analysis": available or manual,
        "asset_analysis_mode": (
            "manual" if manual else "mock" if available else "disabled"
        ),
        "individual_consent_required": True,
        "automatic_liability": False,
        "conditional_policy": "all_consents_before_holds_then_independent_obligations",
        "partial_failure_policy": "preserve_confirmed_reconcile_unknown_release_uncommitted",
    }


def enabled_services_from_env(value):
    value = (value or "none").strip().lower()
    if value == "none":
        return []
    if value == "all":
        return list(SERVICES)
    selected = {part.strip() for part in value.split(",") if part.strip()}
    if not selected or selected - set(SERVICES):
        raise ImproperlyConfigured(
            "ADVANCED_HOUSING_ENABLED_SERVICES must select supported services, "
            "all, or none. Provider-backed services also require provider readiness."
        )
    return [service for service in SERVICES if service in selected]
