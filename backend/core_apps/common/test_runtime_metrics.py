from unittest.mock import Mock, patch
import pytest
from core_apps.common.runtime_metrics import evaluate_incidents, queue_snapshot, record, snapshot
from core_apps.common.runtime_models import RuntimeIncident

@pytest.mark.django_db
def test_unknown_and_low_sample_windows_do_not_resolve_observed_failure():
    report = {"state": "measured", "requests": 100, "error_rate": .05, "memory": {"ratio": .9}, "runtime": {"failures": ["stale"]}}
    evaluate_incidents(report)
    assert RuntimeIncident.objects.filter(state="open").count() == 3
    report.update(state="no_samples", requests=0, error_rate=None, memory={"ratio": None}, runtime=None)
    evaluate_incidents(report)
    assert RuntimeIncident.objects.filter(state="open").count() == 3
    report.update(state="measured", requests=100, error_rate=0, memory={"ratio": .6}, runtime={"failures": []})
    evaluate_incidents(report)
    assert RuntimeIncident.objects.filter(state="open").count() == 0
    report["error_rate"] = .02
    evaluate_incidents(report)
    assert RuntimeIncident.objects.get(code="runtime.api_errors").occurrences == 2


def test_queue_depth_and_age_do_not_inspect_unowned_queues(settings):
    settings.GENERAL_BACKGROUND_ENABLED = True
    settings.CELERY_BROKER_URL = settings.REDIS_URL
    client = Mock()
    client.eval.side_effect = [[2, '100'], [0, ''], [0, ''], [0, '']]
    result = queue_snapshot(client, 300)
    assert result["pending"] == 2 and result["oldest_seconds"] == 200
    assert all(call.args[2].startswith('sokoun-general') for call in client.eval.call_args_list)
    client.eval.side_effect = [[1, ''], [0, ''], [0, ''], [0, '']]
    assert queue_snapshot(client, 300)["oldest_seconds"] is None


def test_long_request_is_not_reported_as_faster_than_observed(settings):
    settings.RUNTIME_METRICS_ENABLED = True
    client = Mock()
    record("GET", "properties/<uuid:pk>/", 200, 90000, client=client, now=1000)
    increments = {call.args[1]: call.args[2] for call in client.pipeline.return_value.hincrby.call_args_list}
    assert increments["duration_ms"] == 90000
    assert increments["latency_overflow"] == 1
    assert "latency_60000" not in increments


@pytest.mark.django_db
def test_empty_measured_queue_resolves_delay_but_unknown_age_does_not():
    report = {"state": "measured", "requests": 0, "error_rate": None,
              "memory": {"ratio": None}, "runtime": None,
              "queue": {"state": "measured", "pending": 1, "oldest_seconds": 190}}
    evaluate_incidents(report)
    assert RuntimeIncident.objects.get(code="runtime.queue_delay").state == "open"
    report["queue"]["oldest_seconds"] = None
    evaluate_incidents(report)
    assert RuntimeIncident.objects.get(code="runtime.queue_delay").state == "open"
    report["queue"]["pending"] = 0
    evaluate_incidents(report)
    assert RuntimeIncident.objects.get(code="runtime.queue_delay").state == "resolved"


@pytest.mark.django_db
def test_overflow_latency_keeps_known_lower_bound_and_alerts(settings):
    settings.RUNTIME_METRICS_ENABLED = True
    settings.GENERAL_BACKGROUND_ENABLED = False
    client = Mock()
    client.pipeline.return_value.execute.return_value = [
        {"requests": "100", "server_errors": "0", "duration_ms": "9000000", "latency_overflow": "100"}
    ]
    report = snapshot(client=client, now=1000)
    assert report["average_ms"] == 90000
    assert report["p95_upper_ms"] is None
    assert report["p95_lower_ms"] == 60000
    evaluate_incidents(report)
    assert RuntimeIncident.objects.get(code="runtime.api_latency").state == "open"


@pytest.mark.django_db
def test_dashboard_observation_records_worker_failure_without_monitor_task():
    from core_apps.admin_api.services.system_service_parts.get_system_health import get_system_health
    report = {"state": "measured", "requests": 0, "error_rate": None,
              "average_ms": None, "window_seconds": 300, "server_errors": 0,
              "memory": {"ratio": None}, "runtime": {"failures": ["worker_stale"]}}
    with patch("core_apps.common.runtime_metrics.snapshot", return_value=report):
        observed = get_system_health()
    assert observed["metrics"]["dbStatus"] == "Reachable"
    assert any(item["code"] == "runtime.scheduler" and item["state"] == "open"
               for item in observed["incidents"])
