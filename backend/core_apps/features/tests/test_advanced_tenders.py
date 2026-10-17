from copy import deepcopy
from datetime import timedelta
from uuid import uuid4
import pytest
from django.test import override_settings
from django.utils import timezone
from core_apps.features.advanced_tender_models import HousingTender, PackageCandidate
from core_apps.features.planning_models import (
    HousingGroup,
    GroupMembership,
    HousingRequest,
)
from core_apps.features.services.housing_tenders.pricing import (
    quote_allocations,
    validate_tiers,
)
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from . import test_rental_phase2 as rental_fixtures
from .test_rental_phase2 import authenticated

rental_participants = rental_fixtures.rental_participants

API = "/api/v1/features/v1/"
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def enabled():
    with override_settings(
        ADVANCED_HOUSING_ENABLED_SERVICES=["collective_tender_planning"]
    ):
        yield


def command(revision=0, **kwargs):
    return {"request_key": str(uuid4()), "expected_revision": revision, **kwargs}


def post(user, route, body, expected=200):
    response = authenticated(user).post(API + route, body, format="json")
    assert response.status_code == expected, response.data
    return response.data


@pytest.fixture
def scenario(rental_participants):
    owner, tenant, peer, prop, offer_id = rental_participants
    prop.rental_inventory["offers"][0]["terms"].update(
        deposit="none",
        rental_period=1,
        suitable_for="all",
        smoking_allowed=False,
        description="Real quote",
        rules=[],
    )
    prop.save()
    group = HousingGroup.objects.create(name="Existing group", capacity=2)
    GroupMembership.objects.create(group=group, user=tenant, role="admin")
    GroupMembership.objects.create(group=group, user=peer, role="member")
    demand = HousingRequest.objects.create(
        user=tenant,
        title="Canonical group demand",
        criteria={"city_id": str(prop.city.id)},
        expires_at=timezone.now() + timedelta(days=20),
    )
    tender = post(
        tenant,
        "housing-tenders/",
        command(
            title="Group tender",
            group_id=str(group.id),
            request_id=str(demand.id),
            roster_revision=group.roster_revision,
            request_revision=demand.revision,
            closes_at=(timezone.now() + timedelta(days=10)).isoformat(),
            execution_mode="independent_participants",
        ),
        201,
    )["resource"]
    start = timezone.localdate() + timedelta(days=12)
    requirement = {
        "rental_scope": "entire_property",
        "start_on": str(start),
        "end_on": str(start + timedelta(days=30)),
        "rent_limit_minor": 2000000,
        "deposit_limit_minor": 0,
        "disclose": True,
        "independent_ack": True,
        "multi_property": True,
        "minimum_completion": 1,
    }
    return owner, tenant, peer, prop, offer_id, group, demand, tender, requirement


def published(s):
    owner, tenant, peer, prop, offer_id, group, demand, tender, req = s
    for user in [tenant, peer]:
        tender = post(
            user,
            f"housing-tenders/{tender['id']}/requirements/",
            command(tender["revision"], requirement=req),
        )["resource"]
    return post(
        tenant, f"housing-tenders/{tender['id']}/publish/", command(tender["revision"])
    )["resource"]


def bid_for(s, tender, *, selections=None, **extra):
    owner, _, _, prop, offer_id, _, _, _, req = s
    body = command(
        snapshot_id=tender["snapshot_id"],
        tender_revision=tender["revision"],
        selections=selections
        or [{"property_id": str(prop.id), "offer_id": offer_id, "offer_revision": 2}],
        start_on=req["start_on"],
        end_on=req["end_on"],
        expires_at=(timezone.now() + timedelta(days=5)).isoformat(),
        minimum_quantity=1,
        combines=True,
        pricing_rule="canonical",
        price_tiers=[],
        reserved_ack=True,
    )
    body.update(extra)
    return body


def package_for(s, tender, bid, person=None):
    return command(
        tender_revision=tender["revision"],
        snapshot_id=tender["snapshot_id"],
        execution_mode="independent_participants",
        allocations=[
            {
                "participant_id": str((person or s[1]).id),
                "line_id": bid["lines"][0]["id"],
            }
        ],
    )


def test_own_requirements_required_sealed_projection_and_replay(scenario):
    owner, tenant, peer, _, _, _, _, tender, req = scenario
    post(
        tenant,
        f"housing-tenders/{tender['id']}/publish/",
        command(tender["revision"]),
        409,
    )
    post(
        tenant,
        f"housing-tenders/{tender['id']}/requirements/",
        command(tender["revision"], participant_id=str(peer.id), requirement=req),
        400,
    )
    body = command(tender["revision"], requirement=req)
    first = post(tenant, f"housing-tenders/{tender['id']}/requirements/", body)
    assert first == post(tenant, f"housing-tenders/{tender['id']}/requirements/", body)
    tender = first["resource"]
    tender = post(
        peer,
        f"housing-tenders/{tender['id']}/requirements/",
        command(tender["revision"], requirement=req),
    )["resource"]
    tender = post(
        tenant, f"housing-tenders/{tender['id']}/publish/", command(tender["revision"])
    )["resource"]
    public = authenticated(owner).get(API + f"housing-tenders/{tender['id']}/").data
    assert public["own_requirement"] is None and public["request_id"] == ""
    assert "rent_limit_minor" not in str(public) and str(tenant.id) not in str(public)


def test_source_and_quote_authority_and_competitor_prices(scenario):
    owner, tenant, peer, prop, _, _, _, _, _ = scenario
    tender = published(scenario)
    post(peer, f"housing-tenders/{tender['id']}/bids/", bid_for(scenario, tender), 403)
    post(owner, f"housing-tenders/{tender['id']}/bids/", bid_for(scenario, tender), 201)
    assert (
        authenticated(peer)
        .get(API + f"housing-tenders/{tender['id']}/bids/")
        .data["results"]
        == []
    )
    # A different eligible owner can read demand, but never competitors' quotes.
    from core_apps.properties.models import Property
    from core_apps.users.models import User

    competitor = User.objects.create_user(
        email="other-owner@example.com", password="x", is_verified=True
    )
    other = deepcopy(prop)
    other.pkid = None
    other.id = uuid4()
    other.owner = competitor
    other.save()
    assert (
        authenticated(competitor)
        .get(API + f"housing-tenders/{tender['id']}/bids/")
        .data["results"]
        == []
    )
    post(
        competitor,
        f"housing-tenders/{tender['id']}/bids/",
        bid_for(scenario, tender),
        404,
    )


def test_overlap_across_bid_lines_and_packages(scenario):
    tender = published(scenario)
    body = bid_for(scenario, tender)
    body["selections"] *= 2
    post(scenario[0], f"housing-tenders/{tender['id']}/bids/", body, 409)
    a = post(
        scenario[0],
        f"housing-tenders/{tender['id']}/bids/",
        bid_for(scenario, tender),
        201,
    )["resource"]
    b = post(
        scenario[0],
        f"housing-tenders/{tender['id']}/bids/",
        bid_for(scenario, tender),
        201,
    )["resource"]
    build = package_for(scenario, tender, a)
    build["allocations"].append(
        {"participant_id": str(scenario[2].id), "line_id": b["lines"][0]["id"]}
    )
    post(scenario[1], f"housing-tenders/{tender['id']}/package-runs/", build, 409)


def test_exact_private_allocation_own_consent_and_disabled_execution(scenario):
    tender = published(scenario)
    bid = post(
        scenario[0],
        f"housing-tenders/{tender['id']}/bids/",
        bid_for(scenario, tender),
        201,
    )["resource"]
    package = post(
        scenario[1],
        f"housing-tenders/{tender['id']}/package-runs/",
        package_for(scenario, tender, bid),
        201,
    )["resource"]
    assert package["unallocated_count"] == 1 and package["execution_available"] is False
    peer = (
        authenticated(scenario[2]).get(API + f"housing-packages/{package['id']}/").data
    )
    assert peer["allocations"] == [] and peer["total_rent_minor"] is None
    body = command(
        package["revision"],
        digest=package["digest"],
        decision="accept",
        independent_ack=True,
    )
    post(scenario[2], f"housing-packages/{package['id']}/consents/", body, 403)
    bad = {**body, "participant_id": str(scenario[2].id)}
    post(scenario[1], f"housing-packages/{package['id']}/consents/", bad, 400)
    agreed = post(scenario[1], f"housing-packages/{package['id']}/consents/", body)
    assert agreed == post(
        scenario[1], f"housing-packages/{package['id']}/consents/", body
    )
    assert agreed["resource"]["status"] == "accepted_for_planning"
    post(
        scenario[1],
        f"housing-packages/{package['id']}/prepare/",
        command(agreed["resource"]["revision"]),
        403,
    )
    from core_apps.features.models import Lease, RentalInventoryDayLock

    assert not Lease.objects.exists() and not RentalInventoryDayLock.objects.exists()


def test_quote_expiry_roster_changes_and_conditional_mode(scenario):
    tender = published(scenario)
    bid = post(
        scenario[0],
        f"housing-tenders/{tender['id']}/bids/",
        bid_for(scenario, tender),
        201,
    )["resource"]
    request = package_for(scenario, tender, bid)
    request["execution_mode"] = "conditional_package"
    post(scenario[1], f"housing-tenders/{tender['id']}/package-runs/", request, 400)
    package = post(
        scenario[1],
        f"housing-tenders/{tender['id']}/package-runs/",
        package_for(scenario, tender, bid),
        201,
    )["resource"]
    from core_apps.features.advanced_tender_models import OwnerBid

    OwnerBid.objects.filter(id=bid["id"]).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    post(
        scenario[1],
        f"housing-packages/{package['id']}/consents/",
        command(
            package["revision"],
            digest=package["digest"],
            decision="accept",
            independent_ack=True,
        ),
        409,
    )
    scenario[5].roster_revision += 1
    scenario[5].save()
    assert (
        authenticated(scenario[1])
        .get(API + f"housing-tenders/{tender['id']}/")
        .data["status"]
        == "review_required"
    )
    post(
        scenario[1],
        f"housing-tenders/{tender['id']}/package-runs/",
        package_for(scenario, tender, bid),
        403,
    )


def test_private_scope_and_budget_are_hard_constraints(scenario):
    req = scenario[-1]
    req["rental_scope"] = "room"
    tender = published(scenario)
    bid = post(
        scenario[0],
        f"housing-tenders/{tender['id']}/bids/",
        bid_for(scenario, tender),
        201,
    )["resource"]
    post(
        scenario[1],
        f"housing-tenders/{tender['id']}/package-runs/",
        package_for(scenario, tender, bid),
        400,
    )


def test_tiers_distinguish_all_units_and_marginal():
    from types import SimpleNamespace

    tiers = validate_tiers(
        "all_units",
        [
            {"from_quantity": 1, "to_quantity": 2, "rent_minor": 400000},
            {"from_quantity": 3, "to_quantity": 4, "rent_minor": 370000},
        ],
        4,
        [400000] * 4,
    )
    lines = [
        SimpleNamespace(id=str(n), offer=SimpleNamespace(rent_minor=400000))
        for n in range(3)
    ]
    bid = SimpleNamespace(
        minimum_quantity=1,
        lines=SimpleNamespace(count=lambda: 4),
        pricing_rule="all_units",
        price_tiers=tiers,
    )
    assert sum(quote_allocations(bid, lines).values()) == 1110000
    bid.pricing_rule = "marginal"
    assert sum(quote_allocations(bid, lines).values()) == 1170000
    bid.minimum_quantity = 4
    from core_apps.features.services.rental_phase2 import RentalConflict

    with pytest.raises(RentalConflict):
        quote_allocations(bid, lines)


def test_disabled_kills_writes_but_preserves_authorized_history(scenario):
    tender = published(scenario)
    post(
        scenario[0],
        f"housing-tenders/{tender['id']}/bids/",
        bid_for(scenario, tender),
        201,
    )
    with override_settings(ADVANCED_HOUSING_ENABLED_SERVICES=[]):
        read = authenticated(scenario[1]).get(API + f"housing-tenders/{tender['id']}/")
        assert read.status_code == 200 and read.data["allowed_actions"] == []
        history = authenticated(scenario[0]).get(API + "housing-tenders/?owner=true")
        assert history.status_code == 200
        assert [item["id"] for item in history.data["results"]] == [tender["id"]]
        assert all(item["allowed_actions"] == [] for item in history.data["results"])
        quotes = authenticated(scenario[0]).get(
            API + f"housing-tenders/{tender['id']}/bids/"
        )
        assert quotes.status_code == 200
        assert quotes.data["results"][0]["allowed_actions"] == []
        assert (
            authenticated(scenario[2])
            .get(API + "housing-tenders/?owner=true")
            .data["results"]
            == []
        )
        post(
            scenario[1],
            f"housing-tenders/{tender['id']}/amend/",
            command(tender["revision"]),
            403,
        )
    scenario[3].is_verified = False
    scenario[3].save()
    history = authenticated(scenario[0]).get(API + "housing-tenders/?owner=true")
    assert history.status_code == 200
    assert [item["id"] for item in history.data["results"]] == [tender["id"]]


def test_leave_rejoin_and_new_members_cannot_read_previous_period(scenario):
    tender = published(scenario)
    bid = post(
        scenario[0],
        f"housing-tenders/{tender['id']}/bids/",
        bid_for(scenario, tender),
        201,
    )["resource"]
    package = post(
        scenario[1],
        f"housing-tenders/{tender['id']}/package-runs/",
        package_for(scenario, tender, bid),
        201,
    )["resource"]
    group = scenario[5]
    membership = group.memberships.get(user=scenario[2])
    membership.joined_revision += 1
    membership.save()
    group.roster_revision += 1
    group.save()
    assert (
        authenticated(scenario[2])
        .get(API + f"housing-tenders/{tender['id']}/")
        .status_code
        == 404
    )
    assert (
        authenticated(scenario[2])
        .get(API + f"housing-packages/{package['id']}/")
        .status_code
        == 404
    )
    assert (
        authenticated(scenario[2]).get(API + "housing-tenders/").data["results"] == []
    )
    post(
        scenario[1],
        f"housing-tenders/{tender['id']}/amend/",
        command(tender["revision"]),
        409,
    )
    from core_apps.users.models import User

    newcomer = User.objects.create_user(
        email="new-member@example.com", password="x", is_verified=True
    )
    GroupMembership.objects.create(
        group=group, user=newcomer, joined_revision=group.roster_revision
    )
    assert (
        authenticated(newcomer)
        .get(API + f"housing-tenders/{tender['id']}/")
        .status_code
        == 404
    )


def test_child_command_receipts_recover_from_parent_and_revoke_after_leave(scenario):
    tender = published(scenario)
    body = bid_for(scenario, tender)
    bid = post(scenario[0], f"housing-tenders/{tender['id']}/bids/", body, 201)[
        "resource"
    ]
    lookup = authenticated(scenario[0]).get(
        API + f"rental-operations/{body['request_key']}/", {"subject_id": tender["id"]}
    )
    assert lookup.status_code == 200, lookup.data
    assert lookup.data["operation_receipt"]["subject_id"] == bid["id"]
    build = package_for(scenario, tender, bid)
    package = post(
        scenario[1], f"housing-tenders/{tender['id']}/package-runs/", build, 201
    )["resource"]
    lookup = authenticated(scenario[1]).get(
        API + f"rental-operations/{build['request_key']}/", {"subject_id": tender["id"]}
    )
    assert (
        lookup.status_code == 200
        and lookup.data["operation_receipt"]["subject_id"] == package["id"]
    )
    membership = scenario[5].memberships.get(user=scenario[1])
    membership.status = "left"
    membership.save()
    denied = authenticated(scenario[1]).get(
        API + f"rental-operations/{build['request_key']}/", {"subject_id": tender["id"]}
    )
    assert denied.status_code == 404


def test_tender_quotes_do_not_escape_through_legacy_offer_surfaces(
    scenario, monkeypatch
):
    tender = published(scenario)
    bid = post(
        scenario[0],
        f"housing-tenders/{tender['id']}/bids/",
        bid_for(scenario, tender),
        201,
    )["resource"]
    # Academic participants legitimately read the request, but this permission
    # does not promote them to a tender decision-maker or expose sealed bids.
    monkeypatch.setattr(
        "core_apps.features.services.student_housing.publication.participant_can_read",
        lambda user, request: True,
    )
    rows = authenticated(scenario[2]).get(
        API + f"housing-requests/{scenario[6].id}/offers/"
    )
    assert rows.status_code == 200 and rows.data["results"] == []
    owner_rows = authenticated(scenario[0]).get(API + "owner-housing-offers/")
    assert owner_rows.status_code == 200 and owner_rows.data["results"] == []
    post(
        scenario[2],
        f"housing-offers/{bid['lines'][0]['housing_offer_id']}/shortlist/",
        command(1, decision="shortlist"),
        404,
    )


def test_quantity_discount_is_exact_and_decline_requires_new_review(scenario):
    owner, tenant, peer, prop, offer_id, *_ = scenario
    tender = published(scenario)
    other = deepcopy(prop)
    other.pkid = None
    other.id = uuid4()
    other.save()
    body = bid_for(
        scenario,
        tender,
        selections=[
            {"property_id": str(p.id), "offer_id": offer_id, "offer_revision": 2}
            for p in [prop, other]
        ],
        pricing_rule="all_units",
        minimum_quantity=2,
        price_tiers=[
            {"from_quantity": 1, "to_quantity": 1, "rent_minor": 1000000},
            {"from_quantity": 2, "to_quantity": 2, "rent_minor": 900000},
        ],
    )
    bid = post(owner, f"housing-tenders/{tender['id']}/bids/", body, 201)["resource"]
    post(
        tenant,
        f"housing-tenders/{tender['id']}/package-runs/",
        package_for(scenario, tender, bid),
        409,
    )
    build = package_for(scenario, tender, bid)
    build["allocations"].append(
        {"participant_id": str(peer.id), "line_id": bid["lines"][1]["id"]}
    )
    package = post(tenant, f"housing-tenders/{tender['id']}/package-runs/", build, 201)[
        "resource"
    ]
    assert package["total_rent_minor"] == 1800000
    assert all(
        x["rent_minor"] == 900000 and x["canonical_terms_match"] is False
        for x in package["allocations"]
    )
    declined = post(
        peer,
        f"housing-packages/{package['id']}/consents/",
        command(
            package["revision"],
            digest=package["digest"],
            decision="decline",
            independent_ack=False,
        ),
    )["resource"]
    assert declined["status"] == "review_required"
    post(
        tenant,
        f"housing-packages/{package['id']}/consents/",
        command(
            declined["revision"],
            digest=package["digest"],
            decision="accept",
            independent_ack=True,
        ),
        409,
    )


def test_current_canonical_terms_revoke_prior_package_acceptance(scenario):
    tender = published(scenario)
    bid = post(
        scenario[0],
        f"housing-tenders/{tender['id']}/bids/",
        bid_for(scenario, tender),
        201,
    )["resource"]
    package = post(
        scenario[1],
        f"housing-tenders/{tender['id']}/package-runs/",
        package_for(scenario, tender, bid),
        201,
    )["resource"]
    prop = scenario[3]
    prop.rental_inventory["offers"][0]["revision"] += 1
    prop.rental_inventory["offers"][0]["terms"]["price"] = "12000"
    prop.save()
    current = (
        authenticated(scenario[1]).get(API + f"housing-packages/{package['id']}/").data
    )
    assert current["status"] == "review_required" and current["allowed_actions"] == []
    post(
        scenario[1],
        f"housing-packages/{package['id']}/consents/",
        command(
            package["revision"],
            digest=package["digest"],
            decision="accept",
            independent_ack=True,
        ),
        409,
    )


def test_unsupported_quote_conditions_are_rejected(scenario):
    tender = published(scenario)
    for extra in [
        {"fees": {"hidden": 100}},
        {"price_period": "weekly"},
        {"currency": "USD"},
        {"additional_charges": [{"amount_minor": 100}]},
    ]:
        body = bid_for(scenario, tender)
        body.update(extra)
        post(scenario[0], f"housing-tenders/{tender['id']}/bids/", body, 400)
