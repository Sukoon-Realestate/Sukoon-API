"""Verify the rendered permissions and collection endpoints used by mobile."""

import pytest

from .test_housing_demand_discovery import publish
from .test_planning_cycles import API, configured_planning_offer
from .test_rental_phase2 import authenticated, rental_participants


@pytest.mark.django_db
def test_capabilities_are_not_the_request_collection(rental_participants):
    owner, tenant, other, prop, _ = rental_participants
    own = publish(tenant, prop)
    elsewhere = publish(other, prop)
    client = authenticated(tenant)
    grant = client.get(
        API + "planning-capabilities/", {"capability": "housing_requests"}
    )
    assert grant.status_code == 200
    permission = grant.json()["data"]
    assert permission["allowed_actions"] == ["read", "publish"]
    assert permission["blocking_reasons"] == []
    assert "results" not in permission

    requests = client.get(API + "housing-requests/", {"page": 1, "page_size": 20})
    assert requests.status_code == 200
    assert [row["id"] for row in requests.json()["data"]] == [own["id"]]
    assert requests.json()["data"][0]["status"] == "published"
    assert requests["X-Total-Count"] == "1"
    assert requests["X-Total-Pages"] == "1"
    assert requests["Cache-Control"] == "private, no-store"

    publish(owner, prop)
    demand = authenticated(owner).get(API + "housing-demand/")
    assert {row["id"] for row in demand.json()["data"]} == {own["id"], elsewhere["id"]}
    assert demand["X-Total-Count"] == "2"
