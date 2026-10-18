"""Normal deployment defaults must work without test-settings feature overrides."""

import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from core_apps.features.services.planning import SERVICES
from .test_rental_phase2 import authenticated, rental_participants


API = "/api/v1/features/v1/"
ALWAYS_READ_SERVICES = ["company_housing", "residential_portfolios"]
CORE_SERVICES = [
    name for name in SERVICES if name not in {"commute", "tenant_assistant"}
]


def deployment_settings(module="production", **environment):
    # Fresh imports exercise the real settings chain. Never read local secrets or
    # inherit a developer's database/provider configuration into this probe.
    script = """
import importlib
import json
import sys
from unittest.mock import patch

with patch("dotenv.load_dotenv"):
    settings = importlib.import_module(sys.argv[1])
names = (
    "PLANNING_ENABLED_SERVICES", "PLANNING_MOCK_DISCOVERY",
    "RENTAL_PROVIDER_BACKEND", "RENTAL_FAKE_PROVIDER_ALLOWED",
    "RENTAL_RUNTIME_ENVIRONMENT",
    "STUDENT_ENABLED_SERVICES", "COMPANY_HOUSING_ENABLED",
)
print(json.dumps({
    **{name: getattr(settings, name) for name in names},
    "planning_schedule": settings.CELERY_BEAT_SCHEDULE["process-planning-jobs"],
    "provider_configured": {
        "routes": bool(settings.PLANNING_ROUTES_API_KEY),
        "gemini": bool(settings.PLANNING_GEMINI_API_KEY and settings.PLANNING_GEMINI_MODEL),
    },
}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script, f"config.settings.{module}"],
        cwd=Path(__file__).resolve().parents[3],
        env={"PATH": os.defpath, **environment},
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    return json.loads(result.stdout)


@pytest.mark.parametrize("module", ["base", "production", "staging"])
@pytest.mark.parametrize("value", [None, "", "  ", "all", " ALL "])
def test_normal_deployment_enables_planning_by_default(module, value):
    environment = {} if value is None else {"PLANNING_ENABLED_SERVICES": value}
    configured = deployment_settings(module, **environment)
    assert configured["PLANNING_ENABLED_SERVICES"] == list(SERVICES)
    assert configured["PLANNING_MOCK_DISCOVERY"] is False
    assert configured["RENTAL_PROVIDER_BACKEND"] == "disabled"
    assert configured["RENTAL_FAKE_PROVIDER_ALLOWED"] is False
    assert configured["planning_schedule"] == {
        "task": "core_apps.features.tasks.process_planning_jobs",
        "schedule": 30.0,
    }


@pytest.mark.parametrize(
    "value,expected",
    [
        ("none", []),
        (" NONE ", []),
        ("housing_groups", ["housing_groups"]),
        ("roommates, lifestyle,roommates,", ["lifestyle", "roommates"]),
        (",".join(SERVICES), list(SERVICES)),
    ],
)
def test_explicit_deployment_selection_and_kill_switch(value, expected):
    assert (
        deployment_settings(PLANNING_ENABLED_SERVICES=value)[
            "PLANNING_ENABLED_SERVICES"
        ]
        == expected
    )


@pytest.mark.parametrize("value", [", ,", "roommate", "none,lifestyle", "all,commute"])
def test_invalid_selection_is_reported_at_startup(value):
    with pytest.raises(subprocess.CalledProcessError) as error:
        deployment_settings(PLANNING_ENABLED_SERVICES=value)
    assert "PLANNING_ENABLED_SERVICES must be" in error.value.stderr


def test_blank_provider_credentials_do_not_claim_readiness():
    configured = deployment_settings(
        PLANNING_ROUTES_API_KEY="  ",
        PLANNING_GEMINI_API_KEY="  ",
        PLANNING_GEMINI_MODEL="  ",
    )
    assert configured["PLANNING_ENABLED_SERVICES"] == list(SERVICES)
    assert configured["provider_configured"] == {"routes": False, "gemini": False}


@pytest.fixture(scope="module")
def normal_configuration():
    return deployment_settings()


@pytest.fixture
def normal_planning(settings, normal_configuration):
    for name, value in normal_configuration.items():
        if name.isupper():
            setattr(settings, name, value)
    # This matrix isolates core planning; student/company readiness has its own suites.
    settings.STUDENT_ENABLED_SERVICES = []
    settings.COMPANY_HOUSING_ENABLED = False
    settings.PLANNING_ROUTES_API_KEY = ""
    settings.PLANNING_GEMINI_API_KEY = ""
    settings.PLANNING_GEMINI_MODEL = ""
    return settings


@pytest.mark.django_db
@pytest.mark.parametrize("capability", CORE_SERVICES)
def test_core_service_grants_work_without_providers(
    normal_planning, rental_participants, capability
):
    tenant = rental_participants[1]
    response = authenticated(tenant).get(
        API + "planning-capabilities/", {"capability": capability, "action": "read"}
    )
    assert response.status_code == 200
    assert response.data["enabled_capabilities"] == ALWAYS_READ_SERVICES + list(SERVICES)
    assert response.data["verified_services"] == ALWAYS_READ_SERVICES + CORE_SERVICES
    assert response.data["allowed_actions"] == ["read"]
    assert response.data["blocking_reasons"] == []
    assert response.data["account_id"] == str(tenant.id)
    assert response.data["expires_at"]
    assert response["Cache-Control"] == "private, no-store"
    assert response.data["configuration"]["commute"]["provider"] == "google_routes"
    assert response.data["configuration"]["assistant"]["provider"] == "gemini"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint",
    [
        "lifestyle-profile/",
        "roommate-candidates/",
        "housing-groups/",
        "housing-requests/",
        "owner-group-applications/",
        "replacement-invitations/",
    ],
)
def test_core_collections_are_accessible_with_normal_defaults(
    normal_planning, rental_participants, endpoint
):
    response = authenticated(rental_participants[1]).get(API + endpoint)
    assert response.status_code == 200, response.data
    assert response["Cache-Control"] == "private, no-store"


@pytest.mark.django_db
def test_normal_defaults_allow_saved_profile_and_preserve_retry_identity(
    normal_planning, rental_participants
):
    client = authenticated(rental_participants[1])
    body = {
        "request_key": str(uuid4()),
        "expected_revision": 0,
        "discoverable": False,
        "habits": {"sleep": "early"},
        "preferences": {},
        "disclosed": [],
    }
    saved = client.post(API + "lifestyle-profile/", body, format="json")
    assert saved.status_code == 200, saved.data
    replay = client.post(API + "lifestyle-profile/", body, format="json")
    assert replay.status_code == saved.status_code and replay.data == saved.data
    current = client.get(API + "lifestyle-profile/").data
    assert current["habits"] == {"sleep": "early"}
    assert current["id"] == saved.data["resource"]["id"]
    stale = client.post(
        API + "lifestyle-profile/", {**body, "request_key": str(uuid4())}, format="json"
    )
    assert stale.status_code == 409
    assert client.get(API + "lifestyle-profile/").data == current


@pytest.mark.django_db
@pytest.mark.parametrize("account", ["guest", "unverified", "inactive"])
def test_default_enablement_preserves_account_requirements(
    normal_planning, rental_participants, account
):
    user = rental_participants[1]
    if account == "guest":
        client = APIClient()
    else:
        if account == "unverified":
            user.is_verified = False
        else:
            user.is_active = False
        user.save()
        client = authenticated(user)
    grant = client.get(API + "planning-capabilities/", {"capability": "lifestyle"})
    assert grant.status_code == 200
    assert grant.data["enabled_capabilities"] == []
    assert grant.data["verified_services"] == []
    assert grant.data["allowed_actions"] == []
    assert grant.data["blocking_reasons"]
    assert client.get(API + "lifestyle-profile/").status_code in {401, 403}


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["none", "housing_groups"])
def test_explicit_disabling_denies_reads_and_writes(
    normal_planning, rental_participants, value
):
    normal_planning.PLANNING_ENABLED_SERVICES = deployment_settings(
        PLANNING_ENABLED_SERVICES=value
    )["PLANNING_ENABLED_SERVICES"]
    client = authenticated(rental_participants[1])
    grant = client.get(API + "planning-capabilities/", {"capability": "lifestyle"})
    assert grant.data["allowed_actions"] == []
    assert "disabled" in grant.data["blocking_reasons"][0]
    assert client.get(API + "lifestyle-profile/").status_code == 403
    assert client.post(API + "lifestyle-profile/", {}, format="json").status_code == 403
    if value == "housing_groups":
        assert client.get(API + "housing-groups/").status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["en", "ar"])
@pytest.mark.parametrize("capability", ["commute", "tenant_assistant"])
def test_missing_provider_reports_setup_without_disabling_other_services(
    normal_planning, rental_participants, capability, language
):
    client = authenticated(rental_participants[1])
    grant = client.get(
        API + "planning-capabilities/",
        {"capability": capability},
        HTTP_ACCEPT_LANGUAGE=language,
    )
    assert capability in grant.data["enabled_capabilities"]
    assert capability not in grant.data["verified_services"]
    assert grant.data["verified_services"] == ALWAYS_READ_SERVICES + CORE_SERVICES
    assert grant.data["allowed_actions"] == []
    assert grant.data["blocking_reasons"] == [
        (
            "This service is awaiting setup."
            if language == "en"
            else "هذه الخدمة في انتظار استكمال الإعداد."
        )
    ]
    assert grant["Content-Language"] == language


@pytest.mark.django_db
@pytest.mark.parametrize(
    "routes,key,model,ready",
    [
        (True, False, False, ["commute"]),
        (False, True, False, []),
        (False, False, True, []),
        (False, True, True, ["tenant_assistant"]),
        (True, True, True, ["commute", "tenant_assistant"]),
    ],
)
def test_provider_capabilities_become_available_independently(
    normal_planning, rental_participants, routes, key, model, ready
):
    normal_planning.PLANNING_ROUTES_API_KEY = "test-only" if routes else ""
    normal_planning.PLANNING_GEMINI_API_KEY = "test-only" if key else ""
    normal_planning.PLANNING_GEMINI_MODEL = "test-only" if model else ""
    client = authenticated(rental_participants[1])
    for capability, action in [("commute", "search"), ("tenant_assistant", "ask")]:
        grant = client.get(API + "planning-capabilities/", {"capability": capability})
        assert grant.data["verified_services"] == ALWAYS_READ_SERVICES + CORE_SERVICES + ready
        assert (action in grant.data["allowed_actions"]) == (capability in ready)
