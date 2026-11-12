"""Search holds no shared locks; commit rejects changed authority and versions."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from django.db import connection, connections
from django.db.models import F

from core_apps.features.transition_network_models import MoveIntent, TransitionCandidate, TransitionMatchRun
from core_apps.features.services.transition_network import jobs
from core_apps.users.models import User
from .test_transition_network import moves as moves_fixture, rental_participants, publish, post, body  # noqa: F401


@pytest.fixture(name="moves")
def prepared_moves(request, settings):
    return moves_fixture.__wrapped__(request.getfixturevalue("rental_participants"), settings)


pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.mvp_deferred]


def queued(moves, monkeypatch):
    monkeypatch.setattr(jobs, "enqueue", lambda _: True)
    _, rows = moves
    for row in rows:
        publish(row)
    intent = MoveIntent.objects.get(id=rows[0][3]["id"])
    run = post(rows[0][0], f"move-intents/{intent.id}/match-runs/", body(intent.revision))["resource"]
    return intent, run


def test_solver_search_runs_outside_atomic_and_records_versioned_inputs(moves, monkeypatch):
    _, run = queued(moves, monkeypatch)
    calculate = jobs.calculate

    def compute(row):
        assert not connection.in_atomic_block
        return calculate(row)

    monkeypatch.setattr(jobs, "calculate", compute)
    assert jobs.process_transition_match(run["id"]) == "result_ready"
    result = TransitionMatchRun.objects.get(id=run["id"])
    assert result.input_snapshot["origin_revision"] == result.input_revision
    assert 0 < len(result.input_snapshot["sources"]) <= 25
    assert len(result.input_snapshot["endpoints"]) <= 12
    import json

    assert len(json.dumps(result.input_snapshot)) < 20000
    assert all(len(value) == 64 for value in result.input_snapshot["sources"].values())
    assert result.candidates.count() == 1


@pytest.mark.parametrize("change", ["pause", "revoke"])
def test_postgres_authority_can_change_during_search_and_commit_fails_closed(moves, monkeypatch, change):
    if connection.vendor != "postgresql":
        pytest.skip("Concurrent current-authority check requires disposable PostgreSQL")
    intent, run = queued(moves, monkeypatch)
    calculated, release = Event(), Event()
    calculate = jobs.calculate

    def compute(row):
        assert not connection.in_atomic_block
        result = calculate(row)
        calculated.set()
        assert release.wait(15)
        return result

    monkeypatch.setattr(jobs, "calculate", compute)

    def worker():
        try:
            return jobs.process_transition_match(run["id"])
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(worker)
        try:
            assert calculated.wait(15)
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '3s'")
            if change == "pause":
                MoveIntent.objects.filter(pk=intent.pk).update(
                    status="paused", matching_consent=False, revision=F("revision") + 1
                )
            else:
                User.objects.filter(pk=intent.user_id).update(is_active=False)
        finally:
            release.set()
        assert future.result(timeout=20) == "result_ready"
    assert TransitionMatchRun.objects.get(id=run["id"]).result_status == "stale"
    assert not TransitionCandidate.objects.filter(run__id=run["id"]).exists()


def test_commit_failure_rolls_back_proposals_and_keeps_job_recoverable(moves, monkeypatch):
    _, run = queued(moves, monkeypatch)
    from core_apps.features.services import advanced_planning_notifications as notices

    record = notices.record

    def fail(*args, **kwargs):
        raise RuntimeError("Injected commit failure")

    monkeypatch.setattr(notices, "record", fail)
    with pytest.raises(RuntimeError, match="Injected commit failure"):
        jobs.process_transition_match(run["id"])
    assert TransitionMatchRun.objects.get(id=run["id"]).status == "queued"
    assert not TransitionCandidate.objects.filter(run__id=run["id"]).exists()
    monkeypatch.setattr(notices, "record", record)
    assert jobs.process_transition_match(run["id"]) == "result_ready"
    assert TransitionCandidate.objects.filter(run__id=run["id"]).count() == 1


def test_old_worker_can_insert_a_run_after_the_additive_migration(moves, monkeypatch):
    from django.db.migrations.loader import MigrationLoader

    intent, _ = queued(moves, monkeypatch)
    apps = MigrationLoader(connection).project_state(("features", "0097_discovery_private_purge_markers")).apps
    OldRun = apps.get_model("features", "TransitionMatchRun")
    legacy = OldRun.objects.create(intent_id=intent.pk, user_id=intent.user_id, input_revision=intent.revision)
    current = TransitionMatchRun.objects.get(pk=legacy.pk)
    assert current.input_snapshot is None
    assert jobs.process_transition_match(str(current.id)) == "result_ready"
    current.refresh_from_db()
    assert current.input_snapshot["origin_revision"] == intent.revision


def test_transition_run_budget(moves, monkeypatch):
    from tools.qa.performance import measured

    _, run = queued(moves, monkeypatch)
    result, report = measured("transition-match-job", 2, lambda: jobs.process_transition_match(run["id"]))
    assert result == "result_ready"
    assert report["http_calls"] == 0
    assert report["max_transaction_seconds"] < 3
    assert report["peak_python_bytes"] < 64 * 1024 * 1024
