"""No provider failure becomes a valid route or silently broadens a reviewed draft."""

from unittest.mock import patch
import pytest
from django.core.cache import cache
from core_apps.features.tests import test_planning_completion as fixtures
from core_apps.features.services.planning_providers import (
    route_matrix,
    DiscoveryUnavailable,
)

pytestmark = pytest.mark.django_db
rental_participants = fixtures.rental_participants


@pytest.fixture(autouse=True)
def providers(settings):
    cache.clear()
    settings.PLANNING_GEMINI_API_KEY = "synthetic-test-key"
    settings.PLANNING_GEMINI_MODEL = "configured-model"
    settings.PLANNING_MOCK_DISCOVERY = False


@pytest.mark.parametrize(
    "element,status",
    [
        ({"status": {"code": 8}}, "unknown"),
        ({"status": {"code": 14}}, "unknown"),
        ({"status": {}, "condition": "ROUTE_NOT_FOUND"}, "no_route"),
        (
            {"status": {}, "condition": "ROUTE_MATRIX_ELEMENT_CONDITION_UNSPECIFIED"},
            "unknown",
        ),
    ],
)
def test_element_failure_does_not_claim_a_route_or_zero_time(element, status):
    destination = {
        "mode": "walking",
        "time_kind": "depart_at",
        "at": "2027-01-01T08:00:00Z",
        "location": {"latitude": 30, "longitude": 31},
    }
    with patch(
        "core_apps.features.services.planning_providers_parts.route_matrix.post_json",
        return_value=[element],
    ):
        result = route_matrix([destination["location"]], destination)[0]
    assert result["duration_seconds"] is None and result["status"] == status


@pytest.mark.parametrize(
    "element",
    [
        {"status": {"code": False}},
        {"status": {"code": "0"}},
        {"destinationIndex": False},
    ],
)
def test_route_indices_and_status_are_typed(element):
    destination = {
        "mode": "walking",
        "time_kind": "depart_at",
        "at": "2027-01-01T08:00:00Z",
        "location": {"latitude": 30, "longitude": 31},
    }
    with patch(
        "core_apps.features.services.planning_providers_parts.route_matrix.post_json",
        return_value=[element],
    ):
        with pytest.raises(DiscoveryUnavailable):
            route_matrix([destination["location"]], destination)


@pytest.mark.parametrize(
    "bad_context",
    [
        {"filters": {"private_contract_notes": "never send"}},
        {"filters": {"price_max": "NaN", "price_period": "monthly"}},
        {"filters": {"amenities": ["invented"]}},
        {"filters": []},
        {"offer_id": "unavailable-offer"},
    ],
)
def test_invalid_context_is_rejected_before_external_inference(
    rental_participants, bad_context
):
    _, tenant, _, prop, _ = rental_participants
    command = fixtures.command(
        text="Find a home",
        language="en",
        retain_history=False,
        session_id="local",
        context={"property_id": str(prop.id), **bad_context},
    )
    with patch(
        "core_apps.features.planning_discovery_views_parts.tenant_assistant_turns.extract_criteria"
    ) as provider:
        response = fixtures.authenticated(tenant).post(
            fixtures.API + "tenant-assistant/turns/", command, format="json"
        )
    assert response.status_code in {400, 409}, response.data
    provider.assert_not_called()


def test_assistant_patch_preserves_reviewed_filters_and_original_offer(
    rental_participants,
):
    _, tenant, _, prop, offer_id = rental_participants
    context = {
        "property_id": str(prop.id),
        "offer_id": offer_id,
        "filters": {
            "city": str(prop.city.id),
            "price_period": "monthly",
            "price_max": "12000",
        },
    }
    command = fixtures.command(
        text="Change only my maximum budget",
        language="en",
        retain_history=False,
        session_id="local",
        context=context,
    )
    with patch(
        "core_apps.features.planning_discovery_views_parts.tenant_assistant_turns.extract_criteria",
        return_value={
            "filters": {"price_max": "11000"},
            "questions": [],
            "unresolved_requirements": [],
        },
    ):
        result = fixtures.post(tenant, "tenant-assistant/turns/", command, 201).data[
            "resource"
        ]
    assert result["filters"] == {**context["filters"], "price_max": "11000"}
    assert all(row["property_id"] == str(prop.id) for row in result["grounded_offers"])
