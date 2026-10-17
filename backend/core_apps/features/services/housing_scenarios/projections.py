from .access import actions
from .snapshots import freshness
from config.advanced_housing import mock_mode_available


def run_payload(run, user):
    return {
        "id": str(run.id),
        "scenario_id": str(run.scenario.id),
        "revision": run.revision,
        "state": run.state,
        "progress": run.progress,
        "failure_code": run.failure_code,
        "input_digest": run.input_digest,
        "result_status": run.result_status,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        **run.result,
        "allowed_actions": (
            ["read", "cancel"] if run.state in {"queued", "running"} else ["read"]
        ),
    }


def payload(scenario, user, *, detailed=True):
    from ..planning import enabled_services

    enabled = enabled_services()
    execution_ready = mock_mode_available() and {
        "corporate_housing_execution",
        "conditional_group_execution",
    } <= set(enabled)
    run = scenario.runs.order_by("-created_at", "-id").first()
    allowed = actions(user, "corporate_housing_simulation", str(scenario.id))
    # Approvers can review the stored snapshot without gaining coordinator source access.
    current = freshness(scenario, user) if "run" in allowed else "not_revalidated"
    return {
        "id": str(scenario.id),
        "company_id": str(scenario.company.id),
        "request_id": str(scenario.request.id),
        "title": scenario.title,
        "revision": scenario.revision,
        "created_at": scenario.created_at.isoformat(),
        "input_digest": scenario.input_digest,
        "source_scenario_id": (
            str(scenario.source_scenario.id) if scenario.source_scenario_id else ""
        ),
        "change_summary": scenario.change_summary,
        "source_freshness": current,
        "input_snapshot": scenario.input_snapshot if detailed else {},
        "result_status": (
            "stale"
            if current == "stale"
            else run.result_status if run else "ready_to_run"
        ),
        "latest_run": (
            {
                "id": str(run.id),
                **run_payload(run, user),
            }
            if run and detailed
            else {}
        ),
        "execution_available": execution_ready,
        "provider_mode": "mock" if mock_mode_available() else "disabled",
        "decisions": [
            {
                "id": str(row.id),
                "status": row.status,
                "revision": row.revision,
                "plan_id": row.plan_id,
            }
            for row in scenario.decisions.order_by("-created_at")
        ],
        "blocking_reason_codes": (
            [] if execution_ready else ["corporate_contract_progression_unavailable"]
        ),
        "allowed_actions": [
            action for action in allowed if action != "run" or current == "current"
        ],
    }
