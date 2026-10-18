"""Availability is readable without reopening quarantined company authority."""

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db
API = "/api/v1/features/v1/"


def test_quarantine_explains_unavailability_without_exposing_company_records(
    user, settings
):
    settings.RECOVERY_TEST_BYPASS = False
    settings.RECOVERY_CONTROL_FILE = ""
    settings.COMPANY_HOUSING_ENABLED = True
    client = APIClient()
    client.force_authenticate(user)
    response = client.get(API + "company-capabilities/")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["available"] is False
    assert data["blocking_reasons"]
    for key in (
        "new_bookings",
        "portfolio_creation",
        "staff_provisioning",
        "activation_email_delivery",
        "account_contexts",
        "assigned_approvals",
        "internal_request_discussions",
        "contracting",
        "payments",
    ):
        assert data[key] is False
    assert response["Cache-Control"] == "private, no-store"
    assert client.get(API + "companies/").status_code == 503
    assert client.post(API + "companies/", {}, format="json").status_code == 503


def test_company_capabilities_still_require_authentication():
    assert APIClient().get(API + "company-capabilities/").status_code == 401


def test_planning_does_not_advertise_quarantined_company_actions(user, settings):
    settings.RECOVERY_TEST_BYPASS = False
    settings.RECOVERY_CONTROL_FILE = ""
    settings.PLANNING_ENABLED_SERVICES = [
        "company_housing",
        "residential_portfolios",
        "housing_groups",
    ]
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    client = APIClient()
    client.force_authenticate(user)
    for capability in ("company_housing", "residential_portfolios"):
        data = client.get(
            API + "planning-capabilities/", {"capability": capability}
        ).json()["data"]
        assert capability not in data["verified_services"]
        assert data["allowed_actions"] == []
        assert data["blocking_reasons"]
        assert "housing_groups" in data["verified_services"]


def test_open_scope_keeps_existing_company_protocol(user, settings):
    settings.RECOVERY_TEST_BYPASS = True
    settings.COMPANY_HOUSING_ENABLED = True
    client = APIClient()
    client.force_authenticate(user)
    data = client.get(API + "company-capabilities/").json()["data"]
    assert data["available"] and data["new_bookings"] and data["portfolio_creation"]
    assert data["blocking_reasons"] == []
    assert data["contracting"] is False and data["payments"] is False
