from django.utils import timezone
from ...housing_scenario_models import HousingScenario, HousingScenarioRun
from ..planning import text_field, check_revision
from ..rental_lifecycle.common import audit
from ..rental_phase2 import fingerprint, RentalConflict
from . import snapshots
from .access import request_for
from .solver import solve, VERSION


def create(user, company, data, source=None):
    snapshot = snapshots.capture(user, company, data)
    changes = []
    if source:
        check_revision(source.revision, data.get("source_revision"))
        changes = [
            key for key in snapshot if source.input_snapshot.get(key) != snapshot[key]
        ]
    scenario = HousingScenario.objects.create(
        company=company,
        request=request_for(user, snapshot["request_id"], write=True),
        created_by=user,
        title=text_field(data, "title", required=True, limit=200),
        input_snapshot=snapshot,
        input_digest=fingerprint(snapshot),
        source_scenario=source,
        change_summary=changes,
    )
    audit(scenario, user, "housing_scenario_created")
    return scenario


def run(user, scenario):
    if snapshots.freshness(scenario, user) != "current":
        raise RentalConflict(
            "The source records changed. Duplicate and review fresh inputs.",
            code="stale_revision",
        )
    result = solve(scenario.input_snapshot)
    HousingScenarioRun.objects.create(
        scenario=scenario,
        created_by=user,
        input_digest=scenario.input_digest,
        solver_version=VERSION,
        result_status=result["result_status"],
        result=result,
        completed_at=timezone.now(),
    )
    scenario.revision += 1
    scenario.save(update_fields=["revision", "updated_at"])
    audit(scenario, user, "housing_scenario_calculated")
    return scenario
