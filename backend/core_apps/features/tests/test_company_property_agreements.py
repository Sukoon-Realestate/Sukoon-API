"""Private package terms are never a public unit price or employee disclosure."""

# flake8: noqa: F401,F811
import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from .test_company_negotiation import (
    cycle,
    company_setup,
    rental_participants,
    policy,
    start,
    act,
    authenticated,
    API,
)

pytestmark = pytest.mark.django_db


def listing(cycle, who="coordinator", **query):
    return authenticated(cycle[who]).get(
        API + "company-terms-negotiations/",
        {
            "workspace": "company",
            "company_id": str(cycle["company"].id),
            "property_id": str(cycle["units"][0].id),
            "active_agreements": "true",
            **query,
        },
    )


def test_property_agreement_keeps_bundle_identity_price_and_current_role(cycle):
    item, _, _ = start(cycle)
    assert listing(cycle).data["results"] == []
    assert act(cycle, item, "owner", "accept").status_code == 200
    item.refresh_from_db()
    for who in ["coordinator", "approver"]:
        response = listing(cycle, who)
        assert response.status_code == 200, response.data
        assert response["Cache-Control"] == "private, no-store"
        (row,) = response.data["results"]
        assert row["id"] == str(item.id)
        assert row["terms"] == item.terms
        assert {v["id"] for v in row["inventory"]["units"]} == {
            str(unit.id) for unit in cycle["units"]
        }
        assert row["inventory"]["offer_id"] == str(item.booking.offer.id)
    for who in ["employee", "reviewer", "owner"]:
        assert listing(cycle, who).data["results"] == []
    assert listing(cycle, property_id=uuid.uuid4()).data["results"] == []
    assert listing(cycle, company_id=uuid.uuid4()).data["results"] == []
    member = cycle["company"].memberships.get(user=cycle["coordinator"])
    member.is_active = False
    member.save(update_fields=["is_active"])
    assert listing(cycle).data["results"] == []


@pytest.mark.parametrize("change", ["capacity", "expired", "followed", "withdrawn"])
def test_old_agreements_leave_property_but_remain_in_history(cycle, change):
    item, _, _ = start(cycle)
    assert act(cycle, item, "owner", "accept").status_code == 200
    assert len(listing(cycle).data["results"]) == 1
    item.refresh_from_db()
    if change == "capacity":
        unit = cycle["units"][0]
        unit.occupancy_capacity += 1
        unit.save(update_fields=["occupancy_capacity"])
    elif change == "expired":
        item.expires_at = timezone.now() - timedelta(seconds=1)
        item.save(update_fields=["expires_at"])
    elif change == "followed":
        item.followed_at = timezone.now()
        item.save(update_fields=["followed_at"])
    else:
        assert (
            act(cycle, item, "owner", "withdraw", reason="Owner withdrawal").status_code
            == 200
        )
    assert listing(cycle).data["results"] == []
    historical = listing(cycle, active_agreements="false")
    assert historical.data["results"][0]["id"] == str(item.id)


@pytest.mark.parametrize(
    "query",
    [
        {"company_id": ""},
        {"property_id": ""},
        {"property_id": "not-a-uuid"},
        {"workspace": "owner"},
        {"active_agreements": "unknown"},
    ],
)
def test_property_query_requires_exact_scope(cycle, query):
    assert listing(cycle, **query).status_code == 400
