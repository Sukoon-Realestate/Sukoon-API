"""Mock staged execution/analysis proof; no assertion claims a live provider result."""

from copy import deepcopy
from datetime import timedelta
import uuid
import pytest
from django.utils import timezone
from core_apps.features.tests.test_advanced_company_passport import (
    scenario_input,
    command,
    observation,
    advanced_enabled,
)
import core_apps.features.tests.test_advanced_company_passport as test_advanced_company_passport_fixtures
import core_apps.features.tests.test_company_housing as test_company_housing_fixtures
from core_apps.features.tests.test_rental_lifecycle import policy
from core_apps.features.tests.test_rental_phase2 import (
    rental_participants,
    authenticated,
)
from core_apps.features.asset_passport_models import (
    AssetObservation,
    AssetAnalysisJob,
    AssetAnalysisSuggestion,
    AssetItem,
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
from core_apps.features.services.asset_passport import analysis

passport = test_advanced_company_passport_fixtures.passport
company_setup = test_company_housing_fixtures.company_setup

API = "/api/v1/features/v1/"


@pytest.fixture(autouse=True)
def mock_mode(settings):
    settings.ADVANCED_HOUSING_PROVIDER_MODE = "mock"
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = [
        "corporate_housing_simulation",
        "corporate_housing_execution",
        "asset_passport",
        "asset_assisted_analysis",
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


def add_observations(passport, *, comparable=True):
    owner, tenant, _, _, lease, report, asset = passport
    item = AssetItem.objects.get(id=asset["id"])
    rows = []
    for offset, condition in ((0, "good"), (1, "worn")):
        media = RentalEvidence.objects.create(
            lease=lease,
            uploader=tenant,
            request_key=uuid.uuid4(),
            original_name="evidence.jpg",
            content_type="image/jpeg",
            size_bytes=4,
            sha256="a" * 64,
            storage_key=str(uuid.uuid4()),
            malware_status="safe",
        )
        report.evidence.add(media)
        row = AssetObservation.objects.create(
            asset=item,
            property=item.property,
            lease=lease,
            author=tenant,
            observed_on=report.inspected_on + timedelta(days=offset),
            condition=condition,
            note="A documented observed symptom without attributed cause.",
            source_kind="condition_report",
            source_id=report.id,
            source_revision=report.revision,
            source_status=report.status,
            capture_context={
                "quality": "comparable" if comparable else "low_light",
                "identity_confirmed": True,
            },
        )
        row.evidence.add(media)
        rows.append(row)
    return rows


@pytest.mark.django_db
def test_analysis_source_snapshot_review_and_new_owner_privacy(passport):
    owner, tenant, stranger, prop, lease, report, asset = passport
    rows = add_observations(passport)
    client = authenticated(tenant)
    response = client.post(
        API + f"asset-items/{asset['id']}/analysis/",
        command(asset["revision"], observation_ids=[str(row.id) for row in rows]),
        format="json",
    )
    assert response.status_code == 200, response.data
    job_id = response.data["resource"]["id"]
    analysis.process.run(job_id)
    job = client.get(API + f"asset-analysis-jobs/{job_id}/").data
    assert job["state"] == "ready_for_review" and job["simulated"]
    assert {f["kind"] for f in job["findings"]} == {
        "possible_reused_evidence",
        "reported_condition_difference",
    }
    finding = job["findings"][-1]
    reviewed = client.post(
        API + f"asset-analysis-findings/{finding['id']}/review/",
        command(
            finding["revision"],
            decision="accepted_as_observation",
            reason="Reviewed the source reports. Inspection still needed.",
        ),
        format="json",
    )
    assert reviewed.status_code == 200, reviewed.data
    assert AssetObservation.objects.count() == 2
    assert reviewed.data["resource"]["output"]["liability_determined"] is False
    prop.owner = stranger
    prop.save()
    assert (
        authenticated(stranger).get(API + f"asset-analysis-jobs/{job_id}/").status_code
        == 404
    )
    assert client.get(API + f"asset-analysis-jobs/{job_id}/").status_code == 200


@pytest.mark.django_db
def test_low_quality_analysis_stays_inconclusive_and_reanalysis_versions(passport):
    _, tenant, _, _, _, _, asset = passport
    rows = add_observations(passport, comparable=False)
    item = AssetItem.objects.get(id=asset["id"])
    first = analysis.create(
        tenant, item, {"observation_ids": [str(row.id) for row in rows]}
    )
    analysis.process.run(str(first.id))
    finding = first.suggestions.get()
    assert finding.kind == "insufficient_comparable_evidence"
    with pytest.raises(Exception):
        analysis.review(
            tenant,
            finding,
            {"decision": "accepted_as_observation", "reason": "Reviewed"},
        )
    analysis.review(
        tenant,
        finding,
        {
            "decision": "inconclusive",
            "reason": "Different lighting prevents comparison.",
        },
    )
    second = analysis.create(
        tenant,
        item,
        {
            "observation_ids": [str(row.id) for row in rows],
            "previous_run_id": str(first.id),
        },
    )
    assert second.pk != first.pk and second.previous_run_id == first.pk
    finding.refresh_from_db()
    assert finding.review_status == "inconclusive"


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
    company_setup, passport, monkeypatch, django_capture_on_commit_callbacks
):
    from core_apps.features.services.housing_scenarios import commands

    _, actor, _, company, *_ = company_setup
    scenario = commands.create(actor, company, scenario_input(company_setup))

    def fail(*args, **kwargs):
        raise RuntimeError("local broker outage")

    monkeypatch.setattr(jobs.calculate, "delay", fail)
    monkeypatch.setattr(analysis.process, "delay", fail)
    rows = add_observations(passport)
    with django_capture_on_commit_callbacks(execute=True):
        jobs.enqueue(actor, scenario)
        job = analysis.create(
            passport[1],
            AssetItem.objects.get(id=passport[-1]["id"]),
            {"observation_ids": [str(row.id) for row in rows]},
        )
    run = scenario.runs.get()
    job.refresh_from_db()
    assert run.state == job.state == "queued"
    assert run.failure_code == job.failure_code == "worker_dispatch_failed"
    jobs.calculate.run(str(run.id))
    analysis.process.run(str(job.id))
    run.refresh_from_db()
    job.refresh_from_db()
    assert run.state == "completed" and job.state == "ready_for_review"


@pytest.mark.django_db
def test_shared_system_case_requires_two_real_units_and_inspection_closure(
    company_setup, passport
):
    from core_apps.features.services.asset_passport import investigations
    from core_apps.features.asset_passport_models import AssetLocationPeriod
    from core_apps.features.planning_models import ConditionReport

    owner, tenant, _, _, lease, report, asset = passport
    building = company_setup[4]
    second_property = company_setup[5][1]
    first = add_observations(passport)[0]
    second_lease = Lease.objects.create(
        property=second_property,
        owner=owner,
        tenant=tenant,
        start_date=lease.start_date,
        end_date=lease.end_date,
        status="active",
        occupancy_status="occupied",
        rent_amount_minor=10000,
        offer_snapshot={"rental_scope": "entire_property"},
    )
    second_report = ConditionReport.objects.create(
        lease=second_lease,
        author=tenant,
        kind="periodic",
        inspected_on=report.inspected_on,
        status="acknowledged",
    )
    second_asset = AssetItem.objects.create(
        property=second_property,
        registered_by=owner,
        label="Supply valve",
        category="fixture",
    )
    AssetLocationPeriod.objects.create(
        asset=second_asset, property=second_property, starts_on=report.inspected_on
    )
    second = AssetObservation.objects.create(
        asset=second_asset,
        property=second_property,
        lease=second_lease,
        author=tenant,
        observed_on=report.inspected_on,
        condition="faulty",
        note="The same reported water pressure symptom needs inspection.",
        source_kind="condition_report",
        source_id=second_report.id,
        source_revision=second_report.revision,
        source_status=second_report.status,
    )
    item = AssetItem.objects.get(id=asset["id"])
    system = investigations.create_system(
        owner,
        item,
        {
            "building_id": str(building.id),
            "asset_ids": [str(item.id), str(second_asset.id)],
            "kind": "water_pressure",
            "name": "Documented supply line",
            "authority_reference": "Owner drawing A7",
        },
    )
    case = investigations.create_case(
        owner,
        system,
        {
            "observation_ids": [str(first.id), str(second.id)],
            "symptom": "water_pressure",
        },
    )
    assert (
        case.state == "investigation_required"
        and not case.hypothesis["cause_confirmed"]
    )
    second_report.status = "draft"
    second_report.save()
    with pytest.raises(Exception):
        investigations.close_case(
            owner,
            case,
            {
                "decision": "common_issue_inspected",
                "source_kind": "condition_report",
                "source_id": str(second_report.id),
                "source_revision": second_report.revision,
                "reason": "Unacknowledged source cannot close investigation.",
            },
        )
    second_report.status = "acknowledged"
    second_report.save()
    closed = investigations.close_case(
        owner,
        case,
        {
            "decision": "inconclusive",
            "source_kind": "condition_report",
            "source_id": str(second_report.id),
            "source_revision": second_report.revision,
            "reason": "Independent inspection did not establish a common cause.",
        },
    )
    assert (
        closed.state == "closed_inconclusive"
        and closed.resolution_source_id == second_report.id
    )
    with pytest.raises(Exception):
        investigations.case_for(tenant, case.id)


@pytest.mark.django_db
def test_warranty_mock_claim_keeps_source_and_never_confirms_coverage(passport):
    from core_apps.features.services.asset_passport import investigations

    owner, _, stranger, prop, _, report, asset = passport
    item = AssetItem.objects.get(id=asset["id"])
    row = investigations.warranty(
        owner,
        item,
        {
            "source_kind": "condition_report",
            "source_id": str(report.id),
            "source_revision": report.revision,
            "issuer": "Recorded issuer",
            "reference": "Document ref A1",
            "starts_on": str(report.inspected_on),
            "ends_on_exclusive": str(report.inspected_on + timedelta(days=365)),
        },
    )
    assert row.status == "recorded_unverified"
    result = investigations.claim(
        owner, row, {"reason": "Please review the supplied source document."}
    )
    assert (
        result.status == "mock_claim_received"
        and not result.mock_result["coverage_confirmed"]
        and not result.mock_result["claim_accepted"]
        and not result.mock_result["money_transferred"]
    )
    report.revision += 1
    report.save()
    with pytest.raises(Exception):
        investigations.claim(
            owner, row, {"reason": "Changed document requires new reference."}
        )
    prop.owner = stranger
    prop.save()
    with pytest.raises(Exception):
        investigations.warranty_for(stranger, row.id)


@pytest.mark.django_db
def test_analysis_revalidates_sources_after_provider_and_stale_claim(
    passport, monkeypatch, settings
):
    _, tenant, _, _, _, report, asset = passport
    rows = add_observations(passport)
    job = analysis.create(
        tenant,
        AssetItem.objects.get(id=asset["id"]),
        {"observation_ids": [str(row.id) for row in rows]},
    )
    original = analysis.mock_compare

    def changed_source(sources):
        report.revision += 1
        report.save()
        return original(sources)

    monkeypatch.setattr(analysis, "mock_compare", changed_source)
    analysis.process.run(str(job.id))
    job.refresh_from_db()
    assert job.state == "failed" and not job.suggestions.exists()
    next_job = analysis.create(
        tenant, job.asset, {"observation_ids": [str(row.id) for row in rows]}
    )

    def reclaimed(sources):
        AssetAnalysisJob.objects.filter(pk=next_job.pk).update(
            state="queued", revision=3
        )
        return original(sources)

    monkeypatch.setattr(analysis, "mock_compare", reclaimed)
    analysis.process.run(str(next_job.id))
    next_job.refresh_from_db()
    assert (
        next_job.state == "queued"
        and next_job.revision == 3
        and not next_job.suggestions.exists()
    )
    settings.ADVANCED_HOUSING_PROVIDER_MODE = "disabled"
    analysis.process.run(str(next_job.id))
    next_job.refresh_from_db()
    assert next_job.state == "queued"


@pytest.mark.django_db
def test_recorded_asset_status_keeps_identity_and_inventory(passport):
    owner, tenant, _, prop, _, _, asset = passport
    original = deepcopy(prop.rental_inventory)
    path = API + f"asset-items/{asset['id']}/update/"
    body = command(
        asset["revision"],
        label="Same physical item",
        category="air_conditioner",
        make_model="Corrected model",
        serial_number="Observed serial",
        status="under_maintenance",
        effective_on=str(timezone.localdate()),
    )
    assert authenticated(tenant).post(path, body, format="json").status_code == 404
    response = authenticated(owner).post(path, body, format="json")
    assert response.status_code == 200, response.data
    assert (
        response.data["resource"]["id"] == asset["id"]
        and response.data["resource"]["status"] == "under_maintenance"
    )
    assert (
        response.data["resource"]["events"][-1]["action"] == "status_under_maintenance"
    )
    prop.refresh_from_db()
    assert prop.rental_inventory == original


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
