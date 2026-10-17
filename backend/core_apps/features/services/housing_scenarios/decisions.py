"""Exact planning decisions and an explicit canonical booking handoff."""

from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from ...housing_scenario_models import (
    HousingScenarioDecision,
    HousingScenarioComparison,
)
from ...company_staff_models import CompanyStaffRecord
from ..planning import text_field
from ..rental_phase2 import RentalConflict, fingerprint
from ..rental_lifecycle.common import audit
from ..company import bookings, approval_routing
from . import access, snapshots
from .solver import validate_plan


def independent(member, scenario):
    if (
        not member
        or not member.is_active
        or not member.is_approver
        or not member.user.is_active
        or not member.user.is_verified
        or member.company_id != scenario.company_id
        or member.user_id
        in {scenario.request.requester_id, scenario.request.coordinator_id}
    ):
        return False
    return (
        not CompanyStaffRecord.objects.filter(
            company=scenario.company,
            id__in=[r["id"] for r in scenario.input_snapshot["staff"]],
        )
        .filter(
            Q(membership__user=member.user) | Q(work_email__iexact=member.user.email)
        )
        .exists()
    )


def for_user(user, identifier, *, lock=False):
    query = HousingScenarioDecision.objects.select_related(
        "scenario__company", "scenario__request", "approver__user", "run"
    )
    if lock:
        query = query.select_for_update(of=("self",))
    decision = get_object_or_404(query, id=identifier)
    if decision.approver.user_id == user.pk and independent(
        decision.approver, decision.scenario
    ):
        return decision
    access.scenario_for(user, decision.scenario.id)
    return decision


def request(user, scenario, data):
    access.scenario_for(user, scenario.id, write=True)
    if snapshots.freshness(scenario, user) != "current":
        raise RentalConflict(
            "The source records changed. Duplicate and review fresh inputs.",
            code="stale_revision",
        )
    run = get_object_or_404(
        scenario.runs,
        id=data.get("run_id"),
        state="completed",
        input_digest=scenario.input_digest,
    )
    plan = next(
        (
            row
            for row in run.result.get("plan_options", [])
            if row["id"] == data.get("plan_id")
        ),
        None,
    )
    if not plan or validate_plan(scenario.input_snapshot, plan):
        raise ValidationError(
            {"plan_id": "Choose an independently validated current plan."}
        )
    approver = scenario.company.default_approver
    if not independent(approver, scenario):
        raise RentalConflict(
            "Assign an active independent approver before submitting this package.",
            code="independent_approver_required",
        )
    snapshot = {
        "scenario_id": str(scenario.id),
        "input_digest": scenario.input_digest,
        "run_id": str(run.id),
        "plan": plan,
        "company_revision": scenario.company.revision,
        "approver_revision": approver.revision,
        "policy_version": "corporate-decision-v2",
    }
    result = HousingScenarioDecision.objects.create(
        scenario=scenario,
        run=run,
        created_by=user,
        approver=approver,
        plan_id=plan["id"],
        snapshot=snapshot,
        snapshot_digest=fingerprint(snapshot),
        expires_at=timezone.now() + timedelta(hours=24),
    )
    audit(result, user, "scenario_decision_requested")
    return result


def decide(user, decision, data):
    if decision.approver.user_id != user.pk or not independent(
        decision.approver, decision.scenario
    ):
        raise PermissionDenied(
            "An independent approver must decide this accommodation package."
        )
    if (
        decision.status != "pending"
        or decision.expires_at <= timezone.now()
        or decision.approver.revision != decision.snapshot["approver_revision"]
        or snapshots.freshness(decision.scenario, decision.created_by) != "current"
    ):
        raise RentalConflict(
            "Refresh and review the current decision snapshot.", code="stale_revision"
        )
    verdict = data.get("decision")
    if verdict not in {"approved", "rejected", "changes_requested"}:
        raise ValidationError(
            {"decision": "Choose approval, rejection, or changes requested."}
        )
    reason = text_field(data, "reason", required=verdict != "approved", limit=1000)
    decision.status, decision.reason, decision.decided_at = (
        verdict,
        reason,
        timezone.now(),
    )
    decision.revision += 1
    decision.save()
    audit(decision, user, "scenario_" + verdict)
    return decision


def prepare(user, decision):
    scenario = access.scenario_for(user, decision.scenario.id, write=True, lock=True)
    if decision.status == "prepared":
        return decision
    if (
        decision.status != "approved"
        or decision.expires_at <= timezone.now()
        or not independent(decision.approver, scenario)
        or snapshots.freshness(scenario, user) != "current"
    ):
        raise RentalConflict(
            "Refresh and review the current decision snapshot.", code="stale_revision"
        )
    plan = decision.snapshot["plan"]
    if validate_plan(scenario.input_snapshot, plan):
        raise RentalConflict(
            "The selected plan no longer satisfies its hard constraints.",
            code="invalid_plan",
        )
    for offer_id in plan["offer_ids"]:
        offer = next(
            row
            for row in scenario.input_snapshot["offers"]
            if row["offer_id"] == offer_id
        )
        staff_ids = [
            row["staff_id"]
            for row in plan["assignments"]
            if row["offer_id"] == offer_id
        ]
        scenario.request.refresh_from_db()
        item = bookings.select_offer(
            user,
            scenario.request.id,
            {
                "expected_revision": scenario.request.revision,
                "offer_id": offer_id,
                "offer_revision": offer["offer_revision"],
                "occupant_ids": [],
                "staff_ids": staff_ids,
            },
        )
        approval_routing.submit(user, item.id, {"expected_revision": item.revision})
        decision.booking_items.add(item)
    decision.status = "prepared"
    decision.revision += 1
    decision.save()
    audit(decision, user, "scenario_canonical_proposals_prepared")
    return decision


def payload(decision, user):
    coordinator = decision.scenario.request.coordinator_id == user.pk
    actions = ["read"]
    if (
        decision.status == "pending"
        and decision.approver.user_id == user.pk
        and independent(decision.approver, decision.scenario)
    ):
        actions.append("decide")
    if decision.status == "approved" and coordinator:
        actions.append("prepare_booking")
    if (
        decision.status == "prepared"
        and coordinator
        and decision.booking_items.exists()
        and not decision.booking_items.exclude(status="approved").exists()
    ):
        actions.append("execute")
    source = decision.scenario.input_snapshot
    summary = {
        "id": str(decision.scenario.id),
        "title": decision.scenario.title,
        "input_snapshot": {
            key: source[key]
            for key in (
                "starts_on",
                "ends_on_exclusive",
                "months",
                "required_headcount",
                "staff",
                "offers",
                "planning_assumptions",
            )
            if key in source
        },
    }
    return {
        "scenario_summary": summary,
        "id": str(decision.id),
        "scenario_id": str(decision.scenario.id),
        "company_id": str(decision.scenario.company.id),
        "request_id": str(decision.scenario.request.id),
        "revision": decision.revision,
        "status": decision.status,
        "plan_id": decision.plan_id,
        "snapshot_digest": decision.snapshot_digest,
        "plan": decision.snapshot["plan"],
        "reason": decision.reason,
        "expires_at": decision.expires_at.isoformat(),
        "booking_items": [
            {"id": str(row.id), "revision": row.revision, "status": row.status}
            for row in decision.booking_items.all()
        ],
        "allowed_actions": actions,
        "independent_approval": True,
        "policy_version": "corporate-decision-v2",
    }


def compare(user, scenario, data):
    others = data.get("scenario_ids", [])
    if not isinstance(others, list) or not 1 <= len(others) <= 2:
        raise ValidationError(
            {"scenario_ids": "Compare two or three authorized scenarios."}
        )
    rows = [scenario] + [access.scenario_for(user, identifier) for identifier in others]
    if len({str(row.id) for row in rows}) != len(rows) or any(
        row.company_id != scenario.company_id or row.request_id != scenario.request_id
        for row in rows
    ):
        raise ValidationError(
            {"scenario_ids": "Compare distinct scenarios for the same company request."}
        )
    snapshots_out = []
    for row in rows:
        run = row.runs.filter(state="completed").order_by("-created_at").first()
        snapshots_out.append(
            {
                "scenario_id": str(row.id),
                "title": row.title,
                "input_digest": row.input_digest,
                "source_freshness": snapshots.freshness(row, user),
                "run_id": str(run.id) if run else "",
                "plan_options": run.result.get("plan_options", []) if run else [],
                "changed_inputs": row.change_summary,
            }
        )
    return HousingScenarioComparison.objects.create(
        scenario=scenario,
        created_by=user,
        snapshot={
            "scenarios": snapshots_out,
            "policy_version": "comparison-v2",
            "realized_savings": False,
        },
    )
