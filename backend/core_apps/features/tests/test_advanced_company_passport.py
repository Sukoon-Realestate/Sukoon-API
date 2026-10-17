"""Synthetic local proof of planning isolation and source-level passport privacy."""

from copy import deepcopy
from datetime import timedelta
from itertools import product
import uuid
import pytest
from django.db import transaction
from django.utils import timezone
from core_apps.features.company_models import (
    CompanyMembership,
    CompanyBudgetReservation,
    CompanyBookingItem,
)
from core_apps.features.company_staff_models import CompanyStaffRecord
from core_apps.features.housing_scenario_models import (
    HousingScenario,
    HousingScenarioRun,
)
from core_apps.features.asset_passport_models import AssetItem, AssetLocationPeriod
from core_apps.features.models import (
    Lease,
    RentalInventoryDayLock,
    ReservationHold,
    RentInvoice,
    RentalEvidence,
    PrivateAccessRevocation,
)
from core_apps.features.planning_models import ConditionReport
from core_apps.features.services.housing_scenarios.solver import solve, validate_plan
from . import test_company_housing as company_fixtures
from . import test_rental_phase2 as rental_fixtures
from core_apps.features.tests.test_rental_lifecycle import policy
from core_apps.features.tests.test_rental_phase2 import authenticated

company_setup = company_fixtures.company_setup
rental_participants = rental_fixtures.rental_participants

API = "/api/v1/features/v1/"


def command(revision=0, **data):
    return {"request_key": str(uuid.uuid4()), "expected_revision": revision, **data}


@pytest.fixture(autouse=True)
def advanced_enabled(settings):
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = [
        "corporate_housing_simulation",
        "asset_passport",
    ]


def scenario_input(setup):
    _, actor, _, company, _, _, offer, request = setup
    staff = [
        CompanyStaffRecord.objects.create(
            company=company,
            display_name=f"Staff {index}",
            work_email=f"staff{index}@example.com",
            proposed_roles=["employee"],
            created_by=actor,
        )
        for index in range(request.headcount)
    ]
    return command(
        title="Bounded plan",
        request_id=str(request.id),
        staff_ids=[str(row.id) for row in staff],
        offer_ids=[str(offer.id)],
        constraints={},
    )


@pytest.mark.django_db
def test_scenario_runs_readonly_and_replays_exact_receipt(company_setup):
    _, actor, _, company, _, _, _, _ = company_setup
    client = authenticated(actor)
    body = scenario_input(company_setup)
    counts = [
        model.objects.count()
        for model in (
            CompanyBookingItem,
            CompanyBudgetReservation,
            RentalInventoryDayLock,
            ReservationHold,
            Lease,
            RentInvoice,
        )
    ]
    response = client.post(
        API + f"companies/{company.id}/housing-scenarios/", body, format="json"
    )
    assert response.status_code == 201, response.data
    item = response.data["resource"]
    assert item["company_id"] == str(company.id)
    assert all(
        row["placement_status"] == "planned" for row in item["input_snapshot"]["staff"]
    )
    assert all(
        row["membership_status"] == "prepared_staff"
        for row in item["input_snapshot"]["staff"]
    )
    run_body = command(item["revision"])
    path = API + f"housing-scenarios/{item['id']}/runs/"
    response = client.post(path, run_body, format="json")
    assert response.status_code == 200, response.data
    from core_apps.features.services.housing_scenarios import jobs

    run = HousingScenarioRun.objects.get(scenario__id=item["id"])
    assert run.state == "queued"
    jobs.calculate.run(str(run.id))
    result = client.get(API + f"housing-scenarios/{item['id']}/").data
    assert result["result_status"] == "optimal"
    plan = result["latest_run"]["plan_options"][0]
    assert plan["full_term_rent_minor"] == 100000 and plan["deposit_minor"] == 20000
    assert plan["commute"]["average_minutes"] is None
    assert validate_plan(result["input_snapshot"], plan) == []
    assert not result["execution_available"]
    assert client.post(path, run_body, format="json").data == response.data
    assert HousingScenarioRun.objects.count() == 1
    assert counts == [
        model.objects.count()
        for model in (
            CompanyBookingItem,
            CompanyBudgetReservation,
            RentalInventoryDayLock,
            ReservationHold,
            Lease,
            RentInvoice,
        )
    ]


@pytest.mark.django_db
def test_scenario_stale_revoked_access_and_history_during_rollout(
    company_setup, settings
):
    _, actor, _, company, _, _, offer, _ = company_setup
    client = authenticated(actor)
    body = scenario_input(company_setup)
    first = client.post(
        API + f"companies/{company.id}/housing-scenarios/", body, format="json"
    ).data["resource"]
    path = API + f"housing-scenarios/{first['id']}/"
    offer.revision += 1
    offer.save()
    assert client.get(path).data["result_status"] == "stale"
    assert (
        client.post(
            path + "runs/", command(first["revision"]), format="json"
        ).status_code
        == 409
    )
    duplicate = {
        **body,
        **command(),
        "source_revision": first["revision"],
        "title": "Fresh plan",
    }
    result = client.post(path + "duplicate/", duplicate, format="json")
    assert result.status_code == 201, result.data
    assert result.data["resource"]["source_scenario_id"] == first["id"]
    assert (
        HousingScenario.objects.get(id=first["id"]).input_snapshot
        == first["input_snapshot"]
    )
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = []
    assert client.get(path).status_code == 200
    assert (
        client.post(
            path + "runs/", command(first["revision"]), format="json"
        ).status_code
        == 403
    )
    CompanyMembership.objects.filter(company=company, user=actor).update(
        is_active=False
    )
    assert client.get(path).status_code == 404


def small_snapshot():
    return {
        "staff": [{"id": "e1"}, {"id": "e2"}, {"id": "e3"}],
        "months": 2,
        "constraints": {
            "rent_limit_minor": 10000,
            "deposit_limit_minor": 1000,
            "allowed_property_ids": {"e1": ["u1", "u3"]},
        },
        "offers": [
            {
                "offer_id": "o1",
                "units": [
                    {"id": "u1", "capacity": 2, "physical_keys": ["bed:a", "bed:b"]}
                ],
                "monthly_rent": {"amount_minor": 200},
                "deposit": {"amount_minor": 500},
            },
            {
                "offer_id": "o2",
                "units": [
                    {"id": "u2", "capacity": 1, "physical_keys": ["property:u2"]}
                ],
                "monthly_rent": {"amount_minor": 100},
                "deposit": {"amount_minor": 100},
            },
            {
                "offer_id": "o3",
                "units": [
                    {"id": "u3", "capacity": 3, "physical_keys": ["property:u3"]}
                ],
                "monthly_rent": {"amount_minor": 400},
                "deposit": {"amount_minor": 10},
            },
        ],
    }


def test_solver_matches_exhaustive_independent_assignments_and_qualifies_limits():
    snapshot = small_snapshot()
    costs = []
    # Independent brute force over employee-to-property assignments, rather than
    # the solver's offer subsets and augmenting matching algorithm.
    for assignment in product(range(3), repeat=3):
        if assignment[0] == 1 or assignment.count(0) > 2 or assignment.count(1) > 1:
            continue
        selected = set(assignment)
        costs.append(
            sum(snapshot["offers"][i]["monthly_rent"]["amount_minor"] for i in selected)
            * 2
        )
    result = solve(snapshot)
    assert result["result_status"] == "optimal"
    assert result["plan_options"][0]["full_term_rent_minor"] == min(costs)
    assert all(validate_plan(snapshot, plan) == [] for plan in result["plan_options"])
    unknown = solve(snapshot, max_subsets=0)
    assert unknown["result_status"] == "unknown"
    incumbent = solve(snapshot, max_subsets=3)
    assert (
        incumbent["result_status"] == "feasible" and not incumbent["optimality_proven"]
    )
    invalid = deepcopy(result["plan_options"][0])
    invalid["assignments"][1] = invalid["assignments"][0]
    assert "employee_coverage_invalid" in validate_plan(snapshot, invalid)
    snapshot["constraints"]["rent_limit_minor"] = 1
    assert solve(snapshot)["result_status"] == "infeasible"


def test_solver_rejects_double_counting_overlapping_aggregate_inventory():
    snapshot = small_snapshot()
    snapshot["offers"] = snapshot["offers"][:1] * 2
    snapshot["offers"][1] = {**snapshot["offers"][1], "offer_id": "overlap"}
    assert solve(snapshot)["result_status"] == "infeasible"


def test_solver_fills_named_capacity_before_flexible_supply():
    snapshot = small_snapshot()
    snapshot["staff"] = [{"id": "e1"}, {"id": "e2"}]
    snapshot["constraints"]["allowed_property_ids"] = {"e1": ["u1", "u2"], "e2": ["u1"]}
    snapshot["offers"] = snapshot["offers"][:2]
    snapshot["offers"][1]["occupancy_policy"] = "named_occupants_required"
    # The initially first flexible offer cannot absorb both employees while
    # leaving the mandatory offer empty. Restrict total affordable combinations.
    snapshot["offers"][0]["units"][0]["capacity"] = 1
    result = solve(snapshot)
    assert result["result_status"] == "optimal"
    plan = result["plan_options"][0]
    assert {r["staff_id"]: r["property_id"] for r in plan["assignments"]} == {
        "e1": "u2",
        "e2": "u1",
    }
    assert validate_plan(snapshot, plan) == []
    snapshot["offers"][1]["units"][0]["capacity"] = 3
    assert solve(snapshot)["result_status"] == "infeasible"


@pytest.mark.django_db
def test_scenario_approver_and_incomplete_staff_cannot_read_or_plan(company_setup):
    _, actor, approver, company, _, _, _, _ = company_setup
    body = scenario_input(company_setup)
    path = API + f"companies/{company.id}/housing-scenarios/"
    first = authenticated(actor).post(path, body, format="json").data["resource"]
    assert (
        authenticated(approver)
        .get(API + f"housing-scenarios/{first['id']}/")
        .status_code
        == 404
    )
    assert (
        authenticated(approver)
        .get(API + f"companies/{company.id}/housing-scenario-sources/staff/")
        .status_code
        == 404
    )
    body["staff_ids"] = body["staff_ids"][:-1]
    body["request_key"] = str(uuid.uuid4())
    assert authenticated(actor).post(path, body, format="json").status_code == 400
    assert HousingScenario.objects.count() == 1


@pytest.fixture
def passport(rental_participants):
    owner, tenant, stranger, prop, _ = rental_participants
    today = timezone.localdate()
    lease = Lease.objects.create(
        property=prop,
        owner=owner,
        tenant=tenant,
        template_id="test",
        template_version="1",
        start_date=today - timedelta(days=30),
        end_date=today + timedelta(days=30),
        rent_amount_minor=10000,
        status="active",
        occupancy_status="occupied",
        offer_snapshot={"rental_scope": "entire_property"},
        legacy_read_only=False,
    )
    report = ConditionReport.objects.create(
        lease=lease,
        author=tenant,
        kind="move_in",
        status="submitted",
        inspected_on=today - timedelta(days=10),
    )
    body = command(
        label="Air conditioner",
        category="air_conditioner",
        effective_on=str(today - timedelta(days=30)),
        space_label="Living room",
    )
    response = authenticated(owner).post(
        API + f"properties/{prop.id}/asset-items/", body, format="json"
    )
    assert response.status_code == 201, response.data
    asset = response.data["resource"]
    return owner, tenant, stranger, prop, lease, report, asset


def observation(report, revision=1, **extra):
    return command(
        revision,
        condition="worn",
        observed_on=str(report.inspected_on),
        source_kind="condition_report",
        source_id=str(report.id),
        source_revision=report.revision,
        note="Observed vibration; cause unknown.",
        evidence_ids=[],
        **extra,
    )


@pytest.mark.django_db
def test_passport_links_authorized_report_and_new_owner_cannot_read_raw_history(
    passport,
):
    owner, tenant, stranger, prop, lease, report, asset = passport
    path = API + f"asset-items/{asset['id']}/"
    result = authenticated(tenant).post(
        path + "observations/", observation(report), format="json"
    )
    assert result.status_code == 200, result.data
    assert result.data["resource"]["observations"][0]["source_id"] == str(report.id)
    assert not result.data["resource"]["observations"][0]["liability_determined"]
    assert authenticated(stranger).get(path).status_code == 404
    prop.owner = stranger
    prop.save()
    continuity = authenticated(stranger).get(path)
    assert continuity.status_code == 200 and continuity.data["observations"] == []
    assert continuity.data["events"] and continuity.data["id"] == asset["id"]
    assert authenticated(stranger).get(path + "sources/").data["results"] == []
    assert len(authenticated(tenant).get(path).data["observations"]) == 1
    PrivateAccessRevocation.objects.create(lease=lease, user=tenant)
    assert authenticated(tenant).get(path).status_code == 404


@pytest.mark.django_db
def test_passport_rejects_foreign_unscanned_and_unlinked_evidence(passport):
    owner, tenant, stranger, prop, lease, report, asset = passport
    evidence = RentalEvidence.objects.create(
        lease=lease,
        uploader=tenant,
        request_key=uuid.uuid4(),
        original_name="private.jpg",
        content_type="image/jpeg",
        size_bytes=3,
        sha256="f" * 64,
        storage_key=str(uuid.uuid4()),
        malware_status="pending",
    )
    report.evidence.add(evidence)
    path = API + f"asset-items/{asset['id']}/observations/"
    body = observation(report)
    body["evidence_ids"] = [str(evidence.id)]
    assert authenticated(owner).post(path, body, format="json").status_code == 400
    evidence.malware_status = "safe"
    evidence.save()
    report.evidence.remove(evidence)
    body["request_key"] = str(uuid.uuid4())
    assert authenticated(owner).post(path, body, format="json").status_code == 400
    report.evidence.add(evidence)
    body["request_key"] = str(uuid.uuid4())
    result = authenticated(owner).post(path, body, format="json")
    assert result.status_code == 200, result.data
    assert "storage_key" not in str(result.data) and "private_content" not in str(
        result.data
    )


@pytest.mark.django_db
@pytest.mark.parametrize("days_before_end, expected", [(1, 200), (0, 400)])
def test_passport_observation_respects_exclusive_tenancy_end(
    passport, days_before_end, expected
):
    owner, tenant, stranger, prop, lease, report, asset = passport
    lease.end_date = timezone.localdate()
    lease.save(update_fields=["end_date"])
    report.inspected_on = lease.end_date - timedelta(days=days_before_end)
    report.save(update_fields=["inspected_on"])
    response = authenticated(tenant).post(
        API + f"asset-items/{asset['id']}/observations/",
        observation(report),
        format="json",
    )
    assert response.status_code == expected, response.data
    assert AssetItem.objects.get(id=asset["id"]).observations.count() == (
        1 if expected == 200 else 0
    )


@pytest.mark.django_db
def test_passport_move_replacement_identity_and_snapshot_history(passport, settings):
    owner, tenant, stranger, prop, lease, report, asset = passport
    client = authenticated(owner)
    path = API + f"asset-items/{asset['id']}/"
    first = client.post(
        path + "observations/", observation(report), format="json"
    ).data["resource"]
    body = command(
        first["revision"],
        property_id=str(prop.id),
        effective_on=str(timezone.localdate()),
        space_label="Bedroom",
    )
    result = client.post(path + "move/", body, format="json")
    assert result.status_code == 200, result.data
    moved = result.data["resource"]
    assert (
        len(moved["locations"]) == 2
        and moved["locations"][0]["space_label"] == "Living room"
    )
    assert moved["observations"] == first["observations"]
    body = command(
        moved["revision"],
        effective_on=str(timezone.localdate()),
        label="New air conditioner",
        category="air_conditioner",
        space_label="Bedroom",
    )
    response = client.post(path + "replace/", body, format="json")
    assert response.status_code == 200, response.data
    replaced = response.data["resource"]
    assert (
        replaced["status"] == "replaced" and replaced["successor_id"] != replaced["id"]
    )
    successor = client.get(API + f"asset-items/{replaced['successor_id']}/").data
    assert (
        successor["predecessor_id"] == asset["id"] and successor["observations"] == []
    )
    assert AssetItem.objects.count() == 2
    assert client.post(path + "replace/", body, format="json").data == response.data
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = []
    assert client.get(path).status_code == 200


@pytest.mark.django_db
def test_passport_room_scope_rejects_other_room_and_unknown_inventory(passport):
    owner, tenant, _, prop, lease, report, asset = passport
    room_a, room_b = str(uuid.uuid4()), str(uuid.uuid4())
    prop.rental_inventory = {
        "rooms": [{"id": room_a, "name": "A"}, {"id": room_b, "name": "B"}]
    }
    prop.save()
    lease.offer_snapshot = {"rental_scope": "room", "room_ids": [room_a]}
    lease.save()
    item = AssetItem.objects.get(id=asset["id"])
    location = AssetLocationPeriod.objects.get(asset=item)
    location.room_id = room_b
    location.save()
    client = authenticated(tenant)
    path = API + f"asset-items/{item.id}/"
    assert client.get(path).status_code == 404
    assert (
        client.post(
            path + "observations/", observation(report), format="json"
        ).status_code
        == 404
    )
    listing = API + f"properties/{prop.id}/asset-items/?lease_id={lease.id}"
    assert client.get(listing).data["results"] == []
    # The owner's authority cannot bind unrelated room evidence to this item.
    assert (
        authenticated(owner)
        .post(path + "observations/", observation(report), format="json")
        .status_code
        == 400
    )
    location.room_id = room_a
    location.save()
    assert client.get(path).status_code == 200
    assert len(client.get(listing).data["results"]) == 1
    assert (
        client.post(
            path + "observations/", observation(report), format="json"
        ).status_code
        == 200
    )
    rooms = authenticated(owner).get(API + f"properties/{prop.id}/asset-spaces/")
    assert [row["id"] for row in rooms.data["results"]] == [room_a, room_b]
    assert client.get(API + f"properties/{prop.id}/asset-spaces/").status_code == 404
    lease.offer_snapshot = {}
    lease.save()
    assert client.get(path).status_code == 404


@pytest.mark.django_db
def test_passport_later_owner_lifecycle_does_not_leak_to_ended_tenant(passport):
    owner, tenant, stranger, prop, lease, report, asset = passport
    lease.end_date = timezone.localdate() - timedelta(days=1)
    lease.save()
    path = API + f"asset-items/{asset['id']}/"
    response = authenticated(owner).post(
        path + "retire/",
        command(1, effective_on=str(timezone.localdate())),
        format="json",
    )
    assert response.status_code == 200, response.data
    result = authenticated(tenant).get(path)
    assert result.status_code == 200
    assert result.data["status"] == "tenancy_history"
    assert result.data["successor_id"] == "" and result.data["locations"] == []
    assert all(row["action"] != "retire" for row in result.data["events"])
