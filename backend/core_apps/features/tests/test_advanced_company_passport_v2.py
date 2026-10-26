"""Mock staged company execution proof; no assertion claims a live provider result."""

from copy import deepcopy
from datetime import timedelta
import uuid
import pytest
from django.utils import timezone
from core_apps.features.tests.test_advanced_company_passport import (
    scenario_input,
    command,
    advanced_enabled,
)
import core_apps.features.tests.test_company_housing as test_company_housing_fixtures
from core_apps.features.tests.test_rental_lifecycle import policy
from core_apps.features.tests.test_rental_phase2 import (
    rental_participants,
    authenticated,
)
from core_apps.features.housing_scenario_models import (
    HousingScenario,
    HousingScenarioRun,
)
from core_apps.features.models import (
    RentalEvidence,
    Lease,
    ReservationHold,
    RentInvoice,
)
from core_apps.features.company_models import (
    CompanyBudgetReservation,
    CompanyBookingItem,
)
from core_apps.features.services.housing_scenarios import jobs
from core_apps.features.services.housing_scenarios.solver import solve, validate_plan

company_setup = test_company_housing_fixtures.company_setup

API = "/api/v1/features/v1/"


@pytest.fixture(autouse=True)
def mock_mode(settings):
    settings.ADVANCED_HOUSING_PROVIDER_MODE = "mock"
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = [
        "corporate_housing_simulation",
        "corporate_housing_execution",
    ]


@pytest.mark.django_db
def test_async_calculation_has_cancel_and_no_canonical_mutations(company_setup):
    _, actor, _, company, prop, _, _, _ = company_setup
    body = scenario_input(company_setup)
    body["planning_assumptions"] = {
        "site_name": "Declared site",
        "latitude": 30.0,
        "longitude": 31.0,
        "rationale": "Authorized hypothetical shift",
        "transport_monthly_minor": 1200,
        "max_commute_minutes": 90,
    }
    client = authenticated(actor)
    created = client.post(
        API + f"companies/{company.id}/housing-scenarios/", body, format="json"
    )
    assert created.status_code == 201, created.data
    scenario = created.data["resource"]
    counts = [
        model.objects.count()
        for model in (
            CompanyBudgetReservation,
            CompanyBookingItem,
            Lease,
            ReservationHold,
            RentInvoice,
        )
    ]
    response = client.post(
        API + f"housing-scenarios/{scenario['id']}/runs/",
        command(scenario["revision"]),
        format="json",
    )
    assert response.status_code == 200, response.data
    run = HousingScenarioRun.objects.get(scenario__id=scenario["id"])
    assert run.state == "queued"
    cancellation = client.post(
        API + f"housing-scenario-runs/{run.id}/cancel/",
        command(run.revision),
        format="json",
    )
    assert cancellation.status_code == 200
    jobs.calculate.run(str(run.id))
    run.refresh_from_db()
    assert run.state == "cancelled" and run.result == {}
    assert counts == [
        model.objects.count()
        for model in (
            CompanyBudgetReservation,
            CompanyBookingItem,
            Lease,
            ReservationHold,
            RentInvoice,
        )
    ]


@pytest.mark.django_db
def test_decision_is_independent_and_prepares_only_canonical_proposals(company_setup):
    _, actor, approver, company, _, _, _, _ = company_setup
    client = authenticated(actor)
    scenario = client.post(
        API + f"companies/{company.id}/housing-scenarios/",
        scenario_input(company_setup),
        format="json",
    ).data["resource"]
    client.post(
        API + f"housing-scenarios/{scenario['id']}/runs/",
        command(scenario["revision"]),
        format="json",
    )
    run = HousingScenarioRun.objects.get(scenario__id=scenario["id"])
    jobs.calculate.run(str(run.id))
    scenario = client.get(API + f"housing-scenarios/{scenario['id']}/").data
    assert scenario["latest_run"]["state"] == "completed"
    response = client.post(
        API + f"housing-scenarios/{scenario['id']}/request-decision/",
        command(scenario["revision"], run_id=str(run.id), plan_id="lowest_rent"),
        format="json",
    )
    assert response.status_code == 200, response.data
    decision = response.data["resource"]
    path = API + f"housing-scenario-decisions/{decision['id']}/"
    assert (
        client.post(
            path + "decide/",
            command(decision["revision"], decision="approved"),
            format="json",
        ).status_code
        == 403
    )
    approved = authenticated(approver).post(
        path + "decide/",
        command(decision["revision"], decision="approved"),
        format="json",
    )
    assert approved.status_code == 200, approved.data
    prepared = client.post(
        path + "prepare-booking/",
        command(approved.data["resource"]["revision"]),
        format="json",
    )
    assert prepared.status_code == 200, prepared.data
    assert prepared.data["resource"]["booking_items"][0]["status"] == "approval_pending"
    assert (
        CompanyBookingItem.objects.count() == 1
        and CompanyBudgetReservation.objects.count() == 0
    )
    assert not Lease.objects.exists()


def test_individual_commute_limit_and_missing_routes_are_hard_constraints():
    from core_apps.features.tests.test_advanced_company_passport import small_snapshot

    snapshot = small_snapshot()
    snapshot["planning_assumptions"] = {
        "max_commute_minutes": 40,
        "routes": {
            "u1": {"minutes": 15},
            "u2": {"minutes": 120},
            "u3": {"minutes": None},
        },
    }
    assert solve(snapshot)["result_status"] == "infeasible"
    snapshot["planning_assumptions"]["routes"]["u3"]["minutes"] = 25
    result = solve(snapshot)
    assert result["result_status"] == "optimal"
    for plan in result["plan_options"]:
        assert (
            validate_plan(snapshot, plan) == []
            and plan["commute"]["maximum_minutes"] <= 40
        )
    snapshot["planning_assumptions"]["unavailable_property_ids"] = ["u3"]
    assert solve(snapshot)["result_status"] == "infeasible"


def corporate_execution_setup(setup):
    from core_apps.users.models import User
    from core_apps.features.company_models import CompanyMembership
    from core_apps.features.company_staff_models import CompanyStaffRecord
    from core_apps.features.services.company import offers, bookings
    from core_apps.features.services.housing_scenarios import (
        commands,
        decisions,
        execution,
    )

    owner, coordinator, approver, company, building, properties, _, request = setup
    CompanyMembership.objects.filter(company=company, user=coordinator).update(
        can_execute_payments=True,
        signing_verified_until=timezone.now() + timedelta(days=7),
        signing_reference="local-fixture",
    )
    body = scenario_input(setup)
    employees = []
    for staff in CompanyStaffRecord.objects.filter(company=company):
        user = User.objects.create_user(
            email=staff.work_email, password="synthetic", is_verified=True
        )
        staff.membership = CompanyMembership.objects.create(
            company=company, user=user, is_employee=True
        )
        staff.save()
        employees.append(user)
    proposals = [
        offers.create_offer(
            owner,
            {
                "scope": "selected_units",
                "unit_ids": [str(prop.id)],
                "monthly_rent_minor": 60000,
                "deposit_minor": 10000,
                "publish": True,
                "occupancy_policy": "reserve_capacity_with_notice",
            },
        )
        for prop in properties
    ]
    body["offer_ids"] = [str(row.id) for row in proposals]
    scenario = commands.create(coordinator, company, body)
    jobs.enqueue(coordinator, scenario)
    run = scenario.runs.get()
    jobs.calculate.run(str(run.id))
    run.refresh_from_db()
    assert run.state == "completed", run.failure_code
    scenario.refresh_from_db()
    decision = decisions.request(
        coordinator, scenario, {"run_id": str(run.id), "plan_id": "lowest_rent"}
    )
    decision = decisions.decide(approver, decision, {"decision": "approved"})
    decision = decisions.prepare(coordinator, decision)
    for item in decision.booking_items.all():
        bookings.decide(
            approver,
            item.id,
            {
                "expected_revision": item.revision,
                "snapshot_digest": item.snapshot_digest,
                "decision": "approved",
            },
        )
    plan = execution.create(coordinator, decision)
    return plan, [owner, coordinator, approver, *employees]


def execution_command(plan, actor, action, **data):
    plan.refresh_from_db()
    result = authenticated(actor).post(
        API + f"advanced-executions/{plan.id}/{action}/",
        command(
            plan.revision,
            digest=plan.digest,
            policy_version=plan.policy_version,
            **data,
        ),
        format="json",
    )
    return result


def consent_and_prepare(plan, actors):
    for actor in actors:
        response = execution_command(plan, actor, "consents", decision="accept")
        assert response.status_code == 200, response.data
    response = execution_command(plan, actors[1], "prepare")
    assert response.status_code == 200, response.data
    assert response.data["resource"]["state"] == "prepared"


@pytest.mark.django_db
def test_two_company_packages_mock_sign_payment_and_uncertain_reconciliation(
    company_setup, settings
):
    settings.ADVANCED_HOUSING_ENABLED_SERVICES += ["conditional_group_execution"]
    plan, actors = corporate_execution_setup(company_setup)
    owner, coordinator, approver, *employees = actors
    consent_and_prepare(plan, actors)
    legs = list(plan.legs.all())
    assert len(legs) == 2 and CompanyBudgetReservation.objects.count() == 2
    assert not Lease.objects.exists() and not RentInvoice.objects.exists()
    # Employee consent covers a placement, never authority to pay the organization invoice.
    denied = execution_command(
        plan, employees[0], "advance", leg_id=str(legs[0].id), step="company_pay"
    )
    assert denied.status_code in {403, 404}, denied.data
    for leg in legs:
        for signer in (owner, coordinator):
            result = execution_command(
                plan, signer, "advance", leg_id=str(leg.id), step="company_sign"
            )
            assert result.status_code == 200, result.data
    first = execution_command(
        plan,
        coordinator,
        "advance",
        leg_id=str(legs[0].id),
        step="company_pay",
        mock_outcome="unknown_after",
    )
    assert (
        first.status_code == 200 and first.data["resource"]["state"] == "unknown"
    ), first.data
    from core_apps.features.models import RentalProviderInstruction

    before = RentalProviderInstruction.objects.count()
    blocked = execution_command(
        plan, coordinator, "advance", leg_id=str(legs[0].id), step="company_pay"
    )
    assert blocked.status_code == 409, blocked.data
    reconciled = execution_command(plan, coordinator, "reconcile")
    assert reconciled.status_code == 200, reconciled.data
    assert RentalProviderInstruction.objects.count() == before
    second = execution_command(
        plan, coordinator, "advance", leg_id=str(legs[1].id), step="company_pay"
    )
    assert second.status_code == 200, second.data
    result = second.data["resource"]
    assert result["state"] == "completed" and result["confirmed_count"] == 2
    assert all(
        row["state"] == "mock_confirmed"
        and not row["actual_occupancy"]
        and row["payer_kind"] == "organization"
        for row in result["legs"]
    )
    assert not Lease.objects.exists() and not RentInvoice.objects.exists()
    assert all(
        row.result["provider_money_transferred"] is False
        for row in RentalProviderInstruction.objects.filter(kind="advanced_company_pay")
    )


@pytest.mark.django_db
def test_company_partial_withdrawal_preserves_signed_leg_and_current_access(
    company_setup, settings
):
    settings.ADVANCED_HOUSING_ENABLED_SERVICES += ["conditional_group_execution"]
    plan, actors = corporate_execution_setup(company_setup)
    owner, coordinator, _, *employees = actors
    consent_and_prepare(plan, actors)
    legs = list(plan.legs.all())
    signed = execution_command(
        plan, owner, "advance", leg_id=str(legs[0].id), step="company_sign"
    )
    assert signed.status_code == 200, signed.data
    uncommitted = execution_command(
        plan, coordinator, "withdraw", leg_id=str(legs[1].id)
    )
    assert uncommitted.status_code == 200, uncommitted.data
    held = CompanyBookingItem.objects.get(id=legs[0].canonical_id)
    released = CompanyBookingItem.objects.get(id=legs[1].canonical_id)
    assert held.status == "held" and released.status == "withdrawn"
    signed_withdrawal = execution_command(
        plan, coordinator, "withdraw", leg_id=str(legs[0].id)
    )
    assert (
        signed_withdrawal.status_code == 200
        and signed_withdrawal.data["resource"]["state"] == "manual_resolution"
    ), signed_withdrawal.data
    reconciled = execution_command(plan, coordinator, "reconcile")
    assert (
        reconciled.status_code == 200
        and reconciled.data["resource"]["state"] == "manual_resolution"
    ), reconciled.data
    held.refresh_from_db()
    assert held.status == "held" and held.hold.status == "active"
    from core_apps.features.company_models import CompanyMembership

    CompanyMembership.objects.filter(
        user=employees[0], company=company_setup[3]
    ).update(is_active=False)
    assert (
        authenticated(employees[0])
        .get(API + f"advanced-executions/{plan.id}/")
        .status_code
        == 404
    )


@pytest.mark.django_db
def test_disabled_jobs_preserve_queue_and_stale_worker_cannot_write(
    company_setup, settings, monkeypatch
):
    from core_apps.features.services.housing_scenarios import commands

    _, actor, _, company, *_ = company_setup
    scenario = commands.create(actor, company, scenario_input(company_setup))
    jobs.enqueue(actor, scenario)
    run = scenario.runs.get()
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = []
    jobs.calculate.run(str(run.id))
    run.refresh_from_db()
    assert run.state == "queued" and run.revision == 1
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = ["corporate_housing_simulation"]
    original = jobs.solve

    def replaced_claim(snapshot, **kwargs):
        HousingScenarioRun.objects.filter(pk=run.pk).update(state="queued", revision=3)
        return original(snapshot, **kwargs)

    monkeypatch.setattr(jobs, "solve", replaced_claim)
    jobs.calculate.run(str(run.id))
    run.refresh_from_db()
    assert run.state == "queued" and run.revision == 3 and run.result == {}
    monkeypatch.setattr(jobs, "solve", original)
    jobs.calculate.run(str(run.id))
    run.refresh_from_db()
    assert run.state == "completed"


@pytest.mark.django_db
def test_broker_failure_leaves_recoverable_queued_jobs(
    company_setup, monkeypatch, django_capture_on_commit_callbacks
):
    from core_apps.features.services.housing_scenarios import commands

    _, actor, _, company, *_ = company_setup
    scenario = commands.create(actor, company, scenario_input(company_setup))

    def fail(*args, **kwargs):
        raise RuntimeError("local broker outage")

    monkeypatch.setattr(jobs.calculate, "delay", fail)
    with django_capture_on_commit_callbacks(execute=True):
        jobs.enqueue(actor, scenario)
    run = scenario.runs.get()
    assert run.state == "queued"
    assert run.failure_code == "worker_dispatch_failed"
    jobs.calculate.run(str(run.id))
    run.refresh_from_db()
    assert run.state == "completed"


def test_declared_arrival_cost_is_a_forecast_not_a_realized_move_count():
    from core_apps.features.tests.test_advanced_company_passport import small_snapshot

    snapshot = small_snapshot()
    snapshot["planning_assumptions"] = {
        "moving_per_person_minor": 1500,
        "transport_monthly_minor": 2000,
        "turnover_per_unit_minor": 500,
    }
    for plan in solve(snapshot)["plan_options"]:
        assert plan["estimated_moving_minor"] == 4500
        assert (
            plan["moving_cost_basis"] == "one_hypothetical_arrival_per_selected_person"
        )
        assert plan["proposed_move_count"] is None
        assert (
            plan["estimated_known_expense_minor"]
            == plan["full_term_rent_minor"]
            + 4500
            + 2000 * snapshot["months"]
            + plan["estimated_turnover_minor"]
        )
        assert plan["deposit_minor"] > 0
