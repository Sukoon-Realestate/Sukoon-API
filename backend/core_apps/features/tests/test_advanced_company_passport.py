"""Synthetic local proof of company planning isolation."""

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
