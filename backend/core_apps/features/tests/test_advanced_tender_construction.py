from copy import deepcopy
from uuid import uuid4
import pytest
from django.test import override_settings
from core_apps.features.advanced_tender_models import TenderPackageRun, OwnerBid
from core_apps.features.services.housing_tenders import construction
from core_apps.features.services.housing_tenders.jobs import process_tender_packages
from core_apps.features.models import Lease, RentalInventoryDayLock
from . import test_advanced_tenders as fixtures
from .test_rental_phase2 import authenticated

scenario = fixtures.scenario
enabled = fixtures.enabled
rental_participants = fixtures.rental_participants
post, command, published, bid_for, package_for, API = (
    fixtures.post,
    fixtures.command,
    fixtures.published,
    fixtures.bid_for,
    fixtures.package_for,
    fixtures.API,
)
pytestmark = pytest.mark.django_db


def two_unit_bid(s, tender):
    prop = deepcopy(s[3])
    prop.pk = None
    prop.id = uuid4()
    prop.title = "Second tender home"
    prop.slug = "second-tender-home"
    prop.save()
    selections = [
        {"property_id": str(p.id), "offer_id": s[4], "offer_revision": 2}
        for p in [s[3], prop]
    ]
    return post(
        s[0],
        f"housing-tenders/{tender['id']}/bids/",
        bid_for(
            s,
            tender,
            selections=selections,
            minimum_quantity=2,
            pricing_rule="all_units",
            price_tiers=[
                {"from_quantity": 1, "to_quantity": 1, "rent_minor": 1000000},
                {"from_quantity": 2, "to_quantity": 2, "rent_minor": 800000},
            ],
        ),
        201,
    )["resource"]


def start(s, tender):
    body = command(
        snapshot_id=tender["snapshot_id"], tender_revision=tender["revision"]
    )
    route = f"housing-tenders/{tender['id']}/automatic-package-runs/"
    first = post(s[1], route, body, 201)
    assert post(s[1], route, body, 201) == first
    return first["resource"]


def test_deterministic_constructor_exact_tiers_without_reservation(scenario):
    tender = published(scenario)
    two_unit_bid(scenario, tender)
    run = start(scenario, tender)
    assert run["status"] == "queued"
    assert process_tender_packages(run["id"]) == "feasible"
    assert process_tender_packages(run["id"]) == "feasible"
    result = TenderPackageRun.objects.get(id=run["id"])
    assert result.result["optimality_proven"] and result.packages.count() == 2
    for package in result.packages.all():
        assert package.total_rent_minor == 1600000
        assert len(package.allocations) == 2 and not package.consents.exists()
        assert {x["rent_minor"] for x in package.allocations} == {800000}
    assert not Lease.objects.exists() and not RentalInventoryDayLock.objects.exists()
    assert (
        authenticated(scenario[0])
        .get(API + f"housing-package-runs/{run['id']}/")
        .status_code
        == 404
    )
    with override_settings(ADVANCED_HOUSING_ENABLED_SERVICES=[]):
        response = authenticated(scenario[1]).get(
            API + f"housing-package-runs/{run['id']}/"
        )
        assert response.status_code == 200 and response.data["status"] == "feasible"


def test_limited_search_is_never_reported_as_infeasible_or_optimal(
    scenario, monkeypatch
):
    tender = published(scenario)
    two_unit_bid(scenario, tender)
    run = start(scenario, tender)
    monkeypatch.setattr(construction, "MAX_NODES", 0)
    assert process_tender_packages(run["id"]) == "limit_reached"
    result = TenderPackageRun.objects.get(id=run["id"])
    assert result.result["search_limited"] and not result.result["optimality_proven"]
    assert not result.packages.exists()


def test_queued_run_rechecks_quotes_and_disabled_worker_preserves_job(scenario):
    tender = published(scenario)
    bid = two_unit_bid(scenario, tender)
    run = start(scenario, tender)
    with override_settings(ADVANCED_HOUSING_ENABLED_SERVICES=[]):
        assert process_tender_packages(run["id"]) == "paused"
    OwnerBid.objects.filter(id=bid["id"]).update(status="withdrawn", revision=2)
    assert process_tender_packages(run["id"]) == "source_changed"
    assert not TenderPackageRun.objects.get(id=run["id"]).packages.exists()


def test_sealed_clarification_does_not_amend_terms_and_replacement_invalidates_package(
    scenario,
):
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
    body = command(
        bid_revision=bid["revision"], text="Please clarify the included service."
    )
    route = f"housing-bids/{bid['id']}/clarifications/"
    note = post(scenario[1], route, body, 201)
    assert post(scenario[1], route, body, 201) == note
    assert OwnerBid.objects.get(id=bid["id"]).revision == bid["revision"]
    assert not note["resource"]["amends_terms"]
    assert authenticated(scenario[2]).get(API + route).status_code == 404
    assert (
        authenticated(scenario[0]).get(API + route).data["results"][0]["text"]
        == body["text"]
    )
    replacement = post(
        scenario[0],
        f"housing-tenders/{tender['id']}/bids/",
        bid_for(
            scenario,
            tender,
            supersedes_id=bid["id"],
            supersedes_revision=bid["revision"],
        ),
        201,
    )["resource"]
    assert replacement["supersedes_id"] == bid["id"]
    old = OwnerBid.objects.get(id=bid["id"])
    assert old.status == "revised" and old.revision == bid["revision"] + 1
    stale = (
        authenticated(scenario[1]).get(API + f"housing-packages/{package['id']}/").data
    )
    assert stale["status"] == "review_required"


def test_one_quote_line_cannot_inflate_quantity_by_reuse(scenario):
    tender = published(scenario)
    bid = post(
        scenario[0],
        f"housing-tenders/{tender['id']}/bids/",
        bid_for(scenario, tender),
        201,
    )["resource"]
    build = package_for(scenario, tender, bid)
    build["allocations"].append(
        {"participant_id": str(scenario[2].id), "line_id": bid["lines"][0]["id"]}
    )
    post(scenario[1], f"housing-tenders/{tender['id']}/package-runs/", build, 400)
