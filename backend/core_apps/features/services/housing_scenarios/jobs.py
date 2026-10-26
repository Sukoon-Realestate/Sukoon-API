"""Durable bounded jobs. Cancellation cancels computation, never a commitment."""

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from ...housing_scenario_models import HousingScenario, HousingScenarioRun
from ..rental_phase2 import RentalConflict
from . import access, snapshots
from .solver import solve, VERSION


def enqueue(user, scenario):
    if snapshots.freshness(scenario, user) != "current":
        raise RentalConflict(
            "The source records changed. Duplicate and review fresh inputs.",
            code="stale_revision",
        )
    if scenario.runs.filter(state__in=["queued", "running"]).exists():
        raise RentalConflict(
            "A calculation is already queued for this scenario.",
            code="calculation_pending",
        )
    run = HousingScenarioRun.objects.create(
        scenario=scenario,
        created_by=user,
        input_digest=scenario.input_digest,
        solver_version=VERSION,
        result_status="unknown",
        state="queued",
        progress=0,
    )
    scenario.revision += 1
    scenario.save(update_fields=["revision", "updated_at"])

    def dispatch():
        try:
            calculate.delay(str(run.id))
        except Exception:
            HousingScenarioRun.objects.filter(pk=run.pk, state="queued").update(
                failure_code="worker_dispatch_failed"
            )

    transaction.on_commit(dispatch)
    return scenario


def cancel(user, run):
    access.scenario_for(user, run.scenario.id, write=True)
    if run.state in {"queued", "running"}:
        run.cancellation_requested = True
        run.state = "cancelled"
        run.revision += 1
        run.completed_at = timezone.now()
        run.save()
    return run


@shared_task(name="advanced_housing.calculate_scenario")
def calculate(identifier):
    from ..planning import enabled_services
    from ..planning_providers import ready_services
    from config.advanced_housing import mock_mode_available

    def ready(snapshot=None):
        return "corporate_housing_simulation" in ready_services(
            enabled_services()
        ) and (
            not (snapshot or {}).get("planning_assumptions", {}).get("simulated")
            or mock_mode_available()
        )

    if not ready():
        return
    with transaction.atomic():
        run = (
            HousingScenarioRun.objects.select_for_update()
            .select_related("scenario", "created_by")
            .get(id=identifier)
        )
        if (
            run.state != "queued"
            or run.cancellation_requested
            or not ready(run.scenario.input_snapshot)
        ):
            return
        run.state, run.progress, run.started_at = "running", 10, timezone.now()
        run.revision += 1
        claim_revision = run.revision
        run.save()
    try:
        access.scenario_for(run.created_by, run.scenario.id, write=True)
        if snapshots.freshness(run.scenario, run.created_by) != "current":
            raise RentalConflict("The source records changed.", code="stale_revision")
        result = solve(
            run.scenario.input_snapshot,
            cancelled=lambda: HousingScenarioRun.objects.filter(
                pk=run.pk, cancellation_requested=True
            ).exists(),
        )
        for plan in result.get("plan_options", []):
            plan["commute"]["calculated_at"] = run.started_at.isoformat()
        with transaction.atomic():
            current = HousingScenarioRun.objects.select_for_update().get(pk=run.pk)
            if (
                current.cancellation_requested
                or current.state != "running"
                or current.revision != claim_revision
            ):
                return
            if not ready(run.scenario.input_snapshot):
                current.state = "queued"
                current.revision += 1
                current.save()
                return
            scenario = HousingScenario.objects.select_for_update().get(
                pk=run.scenario_id
            )
            if snapshots.freshness(scenario, run.created_by) != "current":
                current.state, current.failure_code = "stale", "stale_revision"
            else:
                current.result, current.result_status = result, result["result_status"]
                current.state, current.progress = "completed", 100
                current.failure_code = ""
            current.completed_at = timezone.now()
            current.revision += 1
            current.save()
            scenario.revision += 1
            scenario.save(update_fields=["revision", "updated_at"])
            from ..advanced_planning_notifications import record

            record(current, None, "scenario.result")
    except Exception:
        with transaction.atomic():
            current = (
                HousingScenarioRun.objects.select_for_update()
                .filter(pk=run.pk, state="running", revision=claim_revision)
                .first()
            )
            if current:
                current.state = "failed"
                current.failure_code = "inputs_or_worker_unavailable"
                current.completed_at = timezone.now()
                current.revision += 1
                current.save()
                from ..advanced_planning_notifications import record

                record(current, None, "scenario.failed")
