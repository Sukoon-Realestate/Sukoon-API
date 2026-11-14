"""Housing Scenario command steps; typed adapters retain the HTTP boundary."""

from core_apps.features.services.planning import require_planning
from core_apps.features.services.housing_scenarios import access, decisions
from core_apps.features.housing_scenario_models import HousingScenarioRun
from django.shortcuts import get_object_or_404


def scenario_run_get_load(*, actor, run_id):
    query = HousingScenarioRun.objects.select_related("scenario")
    run = get_object_or_404(query, id=run_id)
    access.scenario_for(actor, run.scenario.id)
    return run


def scenario_run_post_load(*, actor, run_id):
    query = HousingScenarioRun.objects.select_related("scenario")
    query = query.select_for_update(of=("self",))
    run = get_object_or_404(query, id=run_id)
    access.scenario_for(actor, run.scenario.id)
    return run


def scenario_decision_post_apply(item, _, *, action, actor, receipt_data):
    if action == "decide":
        return decisions.decide(actor, item, receipt_data)
    if action == "prepare-booking":
        return decisions.prepare(actor, item)
    require_planning(actor, "corporate_housing_execution")
    from core_apps.features.services.housing_scenarios.execution import create

    return create(actor, item)


def scenario_decision_post_serialize(item, *, action, actor):
    if action == "execute":
        from core_apps.features.services.advanced_execution.projections import payload

        return payload(item, actor)
    return decisions.payload(item, actor)
