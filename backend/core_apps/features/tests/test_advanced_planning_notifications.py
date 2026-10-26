"""Real source commands and workers persist private, repeatable notifications."""

# flake8: noqa: F401,F811
import pytest
from unittest.mock import patch
from django.http import Http404
from rest_framework.exceptions import NotFound
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.planning_notifications_parts.event_copy import (
    event_copy,
)
from core_apps.features.services.advanced_planning_notifications import EVENT_KIND
from core_apps.features.services.housing_tenders.jobs import process_tender_packages
from core_apps.features.services.housing_scenarios import jobs
from core_apps.features.housing_scenario_models import HousingScenarioRun
from core_apps.features.transition_network_models import TransitionCandidate, MoveIntent
from .test_advanced_tenders import scenario, rental_participants, published, post, API
from .test_advanced_tender_construction import two_unit_bid, start
from .test_advanced_company_passport_v2 import (
    company_setup,
    policy,
    scenario_input,
    command,
    authenticated,
)
from .test_transition_network import moves, matching, body, post as move_post

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def enabled(settings):
    settings.ADVANCED_HOUSING_PROVIDER_MODE = "mock"
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = [
        "collective_tender_planning",
        "corporate_housing_simulation",
    ]


def events(source):
    return PlanningEvent.objects.filter(
        destination__event_kind=EVENT_KIND, destination__source_id=str(source)
    )


def test_sealed_bid_and_worker_result_do_not_notify_unrelated_members(scenario):
    tender = published(scenario)
    bid = two_unit_bid(scenario, tender)
    notice = events(bid["id"]).get()
    assert (
        notice.recipient == scenario[1]
        and notice.destination["workspace"] == "individual"
    )
    assert not events(bid["id"]).filter(recipient=scenario[2]).exists()
    assert not {"requirements", "price", "amount", "text"}.intersection(
        notice.destination
    )
    run = start(scenario, tender)
    process_tender_packages(run["id"])
    result = events(run["id"]).get()
    assert result.recipient == scenario[1]
    assert result.destination["target_id"] == tender["id"]
    count = events(run["id"]).count()
    process_tender_packages(run["id"])
    assert events(run["id"]).count() == count
    assert event_copy(result)["title"]
    from core_apps.features.advanced_tender_models import HousingTender

    HousingTender.objects.get(id=tender["id"]).group.memberships.filter(
        user=scenario[1]
    ).update(role="member")
    with pytest.raises((NotFound, Http404)):
        event_copy(result)


def scenario_run(setup):
    actor, company = setup[1], setup[3]
    client = authenticated(actor)
    response = client.post(
        API + f"companies/{company.id}/housing-scenarios/",
        scenario_input(setup),
        format="json",
    )
    assert response.status_code == 201, response.data
    scenario = response.data["resource"]
    response = client.post(
        API + f"housing-scenarios/{scenario['id']}/runs/",
        command(scenario["revision"]),
        format="json",
    )
    assert response.status_code == 200, response.data
    return client, scenario, HousingScenarioRun.objects.get(scenario__id=scenario["id"])


def test_scenario_result_and_independent_decision_use_company_authority(company_setup):
    client, scenario, run = scenario_run(company_setup)
    jobs.calculate.run(str(run.id))
    assert events(run.id).get().destination["company_id"] == str(company_setup[3].id)
    current = client.get(API + f"housing-scenarios/{scenario['id']}/").data
    response = client.post(
        API + f"housing-scenarios/{scenario['id']}/request-decision/",
        command(current["revision"], run_id=str(run.id), plan_id="lowest_rent"),
        format="json",
    )
    assert response.status_code == 200, response.data
    decision = response.data["resource"]
    notice = events(decision["id"]).get()
    assert notice.recipient == company_setup[2]
    assert notice.destination["target_id"] == decision["id"]
    assert notice.destination["action_type"] == "open_scenario_decision"
    assert event_copy(notice)["title"]
    company_setup[3].memberships.filter(user=company_setup[2]).update(is_active=False)
    with pytest.raises((NotFound, Http404)):
        event_copy(notice)


def test_failed_scenario_worker_preserves_failure_and_single_notice(company_setup):
    _, _, run = scenario_run(company_setup)
    with patch(
        "core_apps.features.services.housing_scenarios.jobs.solve",
        side_effect=RuntimeError("Synthetic worker failure"),
    ):
        jobs.calculate.run(str(run.id))
    run.refresh_from_db()
    assert run.state == "failed"
    notice = events(run.id).get()
    assert notice.destination["change_kind"] == "failed"
    jobs.calculate.run(str(run.id))
    assert events(run.id).count() == 1


def test_move_results_and_withdrawal_keep_exact_private_candidate(moves):
    rows, run = matching(moves)
    candidate = TransitionCandidate.objects.get(run__id=run["id"])
    notices = events(candidate.id)
    assert set(notices.values_list("recipient_id", flat=True)) == {
        row[0].pk for row in rows
    }
    assert all(n.destination["target_id"] == str(candidate.id) for n in notices)
    intent = MoveIntent.objects.get(id=rows[0][3]["id"])
    payload = body(intent.revision)
    path = f"move-intents/{intent.id}/withdraw/"
    response = move_post(rows[0][0], path, payload)
    assert move_post(rows[0][0], path, payload) == response
    changes = notices.filter(destination__change_kind__startswith="source_")
    notice = changes.get()
    assert notice.recipient == rows[1][0]
    assert event_copy(notice)["title"]
