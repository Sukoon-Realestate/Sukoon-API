from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .company_models import PortfolioOffer
from .housing_scenario_models import HousingScenario
from .services.planning import planning_api, page, mutate, require_planning
from .services.rental_phase2 import RentalConflict
from .services.housing_scenarios import (
    access,
    commands,
    projections,
    snapshots,
    jobs,
    decisions,
)
from .housing_scenario_models import HousingScenarioRun
from django.shortcuts import get_object_or_404
from django.db.models import Q

CAPABILITY = "corporate_housing_simulation"


@planning_api(["GET"], None)
def decision_inbox(request, company_id):
    from .company_models import Company
    from .housing_scenario_models import HousingScenarioDecision
    from .services.company.access import member_for

    company = get_object_or_404(Company, id=company_id)
    member = member_for(request.user, company)
    query = HousingScenarioDecision.objects.filter(scenario__company=company)
    scope = (
        Q(scenario__request__coordinator=request.user)
        if member.is_coordinator
        else Q(pk__in=[])
    )
    if member.is_approver:
        scope |= Q(approver=member)
    return page(
        request,
        query.filter(scope).order_by("-created_at"),
        lambda row: decisions.payload(
            decisions.for_user(request.user, row.id), request.user
        ),
    )


@planning_api(["GET"], None)
def comparison_detail(request, comparison_id):
    from .housing_scenario_models import HousingScenarioComparison

    row = get_object_or_404(HousingScenarioComparison, id=comparison_id)
    access.scenario_for(request.user, row.scenario.id)
    for item in row.snapshot["scenarios"]:
        access.scenario_for(request.user, item["scenario_id"])
    return Response({"id": str(row.id), "revision": row.revision, **row.snapshot})


@planning_api(["GET", "POST"], None)
def scenarios(request, company_id):
    company = access.company_for(
        request.user, company_id, write=request.method == "POST"
    )
    if request.method == "GET":
        query = (
            HousingScenario.objects.filter(
                company=company, request__in=access.requests_for(request.user, company)
            )
            .select_related("request", "company")
            .order_by("-created_at", "-id")
        )
        return page(
            request,
            query,
            lambda value: projections.payload(value, request.user, detailed=False),
        )
    require_planning(request.user, CAPABILITY)
    return mutate(
        request,
        "housing_scenario.create",
        lambda: access.company_for(request.user, company_id, write=True, lock=True),
        lambda item, _: commands.create(request.user, item, request.data),
        lambda item: projections.payload(item, request.user),
        creating=True,
    )


@planning_api(["GET"], None)
def scenario_detail(request, scenario_id):
    return Response(
        projections.payload(
            access.scenario_for(request.user, scenario_id), request.user
        )
    )


@planning_api(["POST"], None)
def scenario_action(request, scenario_id, action):
    require_planning(request.user, CAPABILITY)
    if action not in {"runs", "duplicate", "request-decision", "compare", "validate"}:
        raise ValidationError({"action": "Choose a supported decision action."})
    return mutate(
        request,
        "housing_scenario." + action,
        lambda: access.scenario_for(request.user, scenario_id, write=True, lock=True),
        lambda item, _: (
            jobs.enqueue(request.user, item)
            if action == "runs"
            else (
                decisions.request(request.user, item, request.data)
                if action == "request-decision"
                else (
                    decisions.compare(request.user, item, request.data)
                    if action == "compare"
                    else (
                        item
                        if action == "validate"
                        else commands.create(
                            request.user, item.company, request.data, source=item
                        )
                    )
                )
            )
        ),
        lambda item: (
            decisions.payload(item, request.user)
            if action == "request-decision"
            else (
                {"id": str(item.id), "revision": item.revision, **item.snapshot}
                if action == "compare"
                else projections.payload(item, request.user)
            )
        ),
        creating=action == "duplicate",
    )


@planning_api(["GET", "POST"], None)
def scenario_run(request, run_id):
    def load():
        query = HousingScenarioRun.objects.select_related("scenario")
        if request.method == "POST":
            query = query.select_for_update(of=("self",))
        run = get_object_or_404(query, id=run_id)
        access.scenario_for(request.user, run.scenario.id)
        return run

    if request.method == "GET":
        return Response(projections.run_payload(load(), request.user))
    require_planning(request.user, CAPABILITY)
    return mutate(
        request,
        "housing_scenario.cancel",
        load,
        lambda run, _: jobs.cancel(request.user, run),
        lambda run: projections.run_payload(run, request.user),
    )


@planning_api(["GET", "POST"], None)
def scenario_decision(request, decision_id, action=""):
    if request.method == "GET":
        return Response(
            decisions.payload(
                decisions.for_user(request.user, decision_id), request.user
            )
        )
    require_planning(request.user, CAPABILITY)
    if action not in {"decide", "prepare-booking", "execute"}:
        raise ValidationError({"action": "Choose a supported decision action."})

    def apply(item, _):
        if action == "decide":
            return decisions.decide(request.user, item, request.data)
        if action == "prepare-booking":
            return decisions.prepare(request.user, item)
        require_planning(request.user, "corporate_housing_execution")
        from .services.housing_scenarios.execution import create

        return create(request.user, item)

    def serialize(item):
        if action == "execute":
            from .services.advanced_execution.projections import payload

            return payload(item, request.user)
        return decisions.payload(item, request.user)

    return mutate(
        request,
        "housing_decision." + action,
        lambda: decisions.for_user(request.user, decision_id, lock=True),
        apply,
        serialize,
    )


@planning_api(["GET"], None)
def scenario_sources(request, company_id, kind):
    company = access.company_for(request.user, company_id, write=True)
    if kind == "requests":
        return page(
            request,
            access.requests_for(request.user, company)
            .filter(coordinator=request.user)
            .order_by("-created_at", "-id"),
            lambda row: {
                "id": str(row.id),
                "title": row.title,
                "revision": row.revision,
                "headcount": row.headcount,
                "starts_on": str(row.starts_on),
                "ends_on_exclusive": str(row.ends_on_exclusive),
                "rent_limit_minor": row.commitment_ceiling_minor,
                "deposit_limit_minor": row.deposit_limit_minor,
            },
        )
    if kind == "staff":
        return page(
            request,
            snapshots.eligible_staff(company),
            lambda row: {
                "id": str(row.id),
                "title": row.display_name,
                "revision": row.revision,
                "status": "active_member" if row.membership_id else "prepared_staff",
            },
        )
    if kind == "offers":
        context = access.request_for(
            request.user, request.query_params.get("request_id"), write=True
        )
        if context.company_id != company.pk:
            raise ValidationError({"request_id": "Choose a request from this company."})

        def offer(row):
            try:
                value = snapshots.offer_snapshot(row, context)
                return {
                    "id": str(row.id),
                    "title": " / ".join(unit["title"] for unit in value["units"]),
                    "revision": row.revision,
                    "selectable": True,
                    "capacity": value["capacity"],
                    "units": [
                        {"id": unit["id"], "title": unit["title"]}
                        for unit in value["units"]
                    ],
                    "monthly_rent_minor": row.monthly_rent_minor,
                    "deposit_minor": row.deposit_minor,
                }
            except (RentalConflict, ValidationError):
                return {
                    "id": str(row.id),
                    "title": str(row.id),
                    "revision": row.revision,
                    "selectable": False,
                    "reason_code": "inventory_requires_review",
                }

        return page(
            request,
            PortfolioOffer.objects.filter(status="published").order_by(
                "monthly_rent_minor", "id"
            ),
            offer,
        )
    raise ValidationError({"kind": "Choose requests, staff, or offers."})
