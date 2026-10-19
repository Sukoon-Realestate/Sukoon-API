"""No independent recovery dependency; normal authority/provider checks remain."""

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db
API = "/api/v1/features/v1/"


def test_missing_recovery_configuration_does_not_block_company_reads(user, settings):
    settings.RECOVERY_TEST_BYPASS = False
    settings.RECOVERY_CONTROL_FILE = ""
    settings.COMPANY_HOUSING_ENABLED = True
    client = APIClient()
    client.force_authenticate(user)
    response = client.get(API + "company-capabilities/")
    data = response.json()["data"]
    assert response.status_code == 200
    assert data["available"] and data["new_bookings"] and data["portfolio_creation"]
    assert data["blocking_reasons"] == []
    assert response["Cache-Control"] == "private, no-store"
    assert client.get(API + "companies/").status_code == 200
    assert client.post(API + "companies/", {}, format="json").status_code in {400, 403}


def test_company_capabilities_still_require_authentication():
    assert APIClient().get(API + "company-capabilities/").status_code == 401


def test_feature_stop_and_missing_real_provider_remain_independent(user, settings):
    settings.COMPANY_HOUSING_ENABLED = False
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    client = APIClient()
    client.force_authenticate(user)
    data = client.get(API + "company-capabilities/").json()["data"]
    assert data["available"] and not data["new_bookings"]
    assert data["account_contexts"] and data["tenancy_servicing"]
    assert data["payments"] is False and data["provider_mode"] == "unavailable"
