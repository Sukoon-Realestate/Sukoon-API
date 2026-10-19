from copy import deepcopy
import pytest
from scripts.company_probe_plan import build


def test_probe_plan_cannot_change_api_or_consume_business_backlog():
    spec = {
        "name": "sukoon-app",
        "services": [
            {
                "name": "sukoon-api",
                "github": {"repo": "Sukoon-Realestate/Sukoon-API", "branch": "main"},
                "envs": [{"key": "SECRET_KEY", "value": "synthetic", "type": "SECRET"}],
            }
        ],
        "databases": [{"name": "existing"}],
    }
    original = deepcopy(spec)
    result = build(spec)
    assert spec == original and result["services"] == original["services"]
    assert result["databases"] == original["databases"] and "jobs" not in result
    assert len(result["workers"]) == 2
    worker = result["workers"][0]
    assert "--queues=sokoun-background-probe" in worker["run_command"]
    assert {v["key"]: v["value"] for v in worker["envs"]}[
        "DJANGO_SETTINGS_MODULE"
    ] == "config.settings.background_probe"
    with pytest.raises(ValueError):
        build(result)


@pytest.mark.django_db(transaction=True)
def test_probe_executes_only_read_only_database_statement():
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from core_apps.common.tasks import background_probe

    with CaptureQueriesContext(connection) as captured:
        assert background_probe.run() == {"database_read": 1, "business_writes": 0}
    queries = [q["sql"].strip().upper() for q in captured.captured_queries]
    assert "SET LOCAL TRANSACTION READ ONLY" in queries
    assert not any(
        q.startswith(("INSERT", "UPDATE", "DELETE", "ALTER", "TRUNCATE"))
        for q in queries
    )
