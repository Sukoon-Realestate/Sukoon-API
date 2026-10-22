import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from celery import Celery
from celery.beat import ScheduleEntry
from django.test import RequestFactory

from config import runtime
from core_apps.common.runtime_views import health

SHA = "a" * 40
TASK = "core_apps.features.tasks.scan_rental_evidence"


class MemoryRedis:
    def __init__(self):
        self.values = {}

    def set(self, key, value, ex=None):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)


@pytest.fixture
def runtime_settings(settings):
    settings.RUNTIME_EVIDENCE_ENABLED = True
    settings.RUNTIME_EVIDENCE_NAMESPACE = "isolated-runtime-test"
    settings.SOKOUN_RELEASE_SHA = SHA
    settings.CELERY_BEAT_SCHEDULE = {"scan": {"task": TASK, "schedule": 60.0}}
    return settings


def scheduled_task(*, eager=False, direct=False, headers=None):
    return SimpleNamespace(
        name=TASK,
        request=SimpleNamespace(
            is_eager=eager,
            called_directly=direct,
            headers={"sokoun_schedule": "scan"} if headers is None else headers,
            hostname="worker-test",
        ),
    )


def dispatch(client, **overrides):
    marker = {
        "schedule": "scan",
        "task": TASK,
        "task_id": "task-1",
        "scheduler_id": "beat-1",
        "scheduler_release_sha": SHA,
        "scheduler_configuration": runtime.configuration_identity(),
        "dispatched_at": 100,
        **overrides,
    }
    runtime.write_record(client, "dispatch:task-1", marker)


def record(client, **overrides):
    marker = {
        "schedule": "scan",
        "task": TASK,
        "task_id": "task-1",
        "scheduler_id": "beat-1",
        "scheduler_release_sha": SHA,
        "scheduler_configuration": runtime.configuration_identity(),
        "worker_release_sha": SHA,
        "worker_configuration": runtime.configuration_identity(),
        "dispatched_at": 100,
        "completed_at": 110,
        "state": "SUCCESS",
        "counts": {"safe": 1},
        **overrides,
    }
    runtime.write_record(client, "execution:scan", marker)


def live_beat(client):
    runtime.write_record(
        client,
        "beat",
        {
            "scheduler_id": "beat-1",
            "release_sha": SHA,
            "configuration": runtime.configuration_identity(),
            "at": 120,
        },
    )
    client.set(runtime.key("beat-lease"), "beat-1")


@pytest.mark.parametrize(
    "eager,direct,headers",
    [(True, False, None), (False, True, None), (False, False, {})],
)
def test_local_or_unmarked_tasks_cannot_certify_scheduled_execution(
    runtime_settings, eager, direct, headers
):
    with patch.object(runtime, "redis_client") as connect:
        runtime.record_scheduled_execution(
            task=scheduled_task(eager=eager, direct=direct, headers=headers),
            task_id="task-1",
            state="SUCCESS",
        )
    connect.assert_not_called()


def test_missing_dispatch_cannot_certify_scheduled_execution(runtime_settings):
    client = MemoryRedis()
    with patch.object(runtime, "redis_client", return_value=client):
        runtime.record_scheduled_execution(
            task=scheduled_task(), task_id="task-1", state="SUCCESS"
        )
    assert not client.values


def test_worker_records_actual_completion_and_only_safe_counts(runtime_settings):
    client = MemoryRedis()
    dispatch(client)
    with patch.object(runtime, "redis_client", return_value=client), patch.object(
        runtime.time, "time", return_value=110
    ):
        runtime.record_scheduled_execution(
            task=scheduled_task(),
            task_id="task-1",
            state="SUCCESS",
            retval={
                "safe": 2,
                "token": "do-not-store",
                "document": b"private",
                "other": {"a": 1},
                "bad name": 10,
            },
        )
    result = json.loads(client.get(runtime.key("execution:scan")))
    assert result["state"] == "SUCCESS"
    assert result["worker_release_sha"] == SHA
    assert result["counts"] == {"safe": 2}
    assert "do-not-store" not in json.dumps(result)


def test_evidence_failure_never_retries_a_completed_business_task(
    runtime_settings, caplog
):
    with patch.object(
        runtime,
        "redis_client",
        side_effect=RuntimeError("redis://password-must-not-log"),
    ):
        runtime.record_scheduled_execution(
            task=scheduled_task(), task_id="task-1", state="SUCCESS"
        )
    assert "RuntimeError" in caplog.text
    assert "password-must-not-log" not in caplog.text


def test_scheduled_report_requires_current_release_after_deployment(runtime_settings):
    client = MemoryRedis()
    live_beat(client)
    record(client)
    assert (
        runtime.execution_report(client, expected_sha=SHA, since=100, now=120)[
            "failures"
        ]
        == []
    )
    assert runtime.execution_report(client, expected_sha=SHA, since=101, now=120)[
        "failures"
    ]
    assert runtime.execution_report(client, expected_sha="b" * 40, now=120)["failures"]


@pytest.mark.parametrize(
    "change",
    [
        {"state": "FAILURE"},
        {"state": "RETRY"},
        {"worker_release_sha": "b" * 40},
        {"scheduler_release_sha": "b" * 40},
        {"scheduler_configuration": {}},
        {"worker_configuration": {}},
        {"task": "another_task"},
        {"completed_at": 1000},
    ],
)
def test_incomplete_or_mismatched_completion_does_not_pass(runtime_settings, change):
    client = MemoryRedis()
    live_beat(client)
    record(client, **change)
    assert runtime.execution_report(client, expected_sha=SHA, now=120)["failures"] == [
        "scheduled_execution_unverified:scan"
    ]


def test_stale_worker_and_scheduler_evidence_does_not_pass(runtime_settings):
    client = MemoryRedis()
    live_beat(client)
    record(client)
    report = runtime.execution_report(client, expected_sha=SHA, now=1000)
    assert "scheduler_missing_or_stale" in report["failures"]
    assert "scheduled_execution_unverified:scan" in report["failures"]


def test_changed_lease_owner_is_not_a_live_scheduler(runtime_settings):
    client = MemoryRedis()
    live_beat(client)
    record(client)
    client.set(runtime.key("beat-lease"), "replacement-beat")
    assert runtime.execution_report(client, expected_sha=SHA, now=120)["failures"] == [
        "scheduler_lease_missing"
    ]


def test_lost_beat_lease_does_not_publish(runtime_settings):
    client = Mock()
    client.eval.return_value = False
    with patch.object(runtime, "redis_client", return_value=client):
        scheduler = runtime.LeaseScheduler(app=Celery("runtime-test"), lazy=True)
    entry = ScheduleEntry(name="scan", task=TASK, schedule=60)
    with patch("celery.beat.Scheduler.apply_async") as publish:
        with pytest.raises(RuntimeError, match="lease was lost"):
            scheduler.apply_async(entry)
    publish.assert_not_called()


def test_beat_marks_published_id_without_overwriting_schedule_options(runtime_settings):
    client = Mock()
    client.eval.return_value = True
    with patch.object(runtime, "redis_client", return_value=client):
        scheduler = runtime.LeaseScheduler(app=Celery("runtime-test"), lazy=True)
    original = {"queue": "celery", "headers": {"retained": True}}
    entry = ScheduleEntry(name="scan", task=TASK, schedule=60, options=original)
    published = []
    with patch(
        "celery.beat.Scheduler.apply_async",
        side_effect=lambda item, **kwargs: published.append(dict(item.options)),
    ):
        scheduler.apply_async(entry)
    assert entry.options is original
    assert published[0]["task_id"]
    headers = published[0]["headers"]
    assert set(headers) == {"retained", "sokoun_schedule", "sokoun_dispatched_at"}
    assert headers["retained"] is True and headers["sokoun_schedule"] == "scan"
    assert isinstance(headers["sokoun_dispatched_at"], float) and headers["sokoun_dispatched_at"] > 0
    dispatch_json = json.loads(client.set.call_args.args[1])
    assert dispatch_json["task_id"] == published[0]["task_id"]


@pytest.mark.django_db
def test_health_checks_dependencies_without_exposing_failure_details():
    with patch("core_apps.common.runtime_views.redis_client") as connect:
        connect.return_value.ping.return_value = True
        response = health(RequestFactory().get("/health/"))
        assert response.status_code == 200
        assert json.loads(response.content) == {"ready": True}
        connect.side_effect = RuntimeError("private redis password")
        response = health(RequestFactory().get("/health/"))
        assert response.status_code == 503
        assert json.loads(response.content) == {"ready": False}
