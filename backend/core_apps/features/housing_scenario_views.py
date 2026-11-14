from functools import partial
from .services.housing_scenarios import entry_commands as entry_commands

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .company_models import PortfolioOffer
from .housing_scenario_models import HousingScenario
from .services.planning import page, mutate, require_planning
from .services.rental_phase2 import RentalConflict
from .services.housing_scenarios import (
    access,
    commands,
    projections,
    snapshots,
    jobs,
    decisions,
)
from django.shortcuts import get_object_or_404
from django.db.models import Q

CAPABILITY = "corporate_housing_simulation"


class DecisionInboxView(FeatureAPIView):
    name = "Decision Inbox"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "housing_scenario_views",
            "decision_inbox",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
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


# Stable callable import for integrations; URLs use the explicit class.
decision_inbox = DecisionInboxView.as_view()


class ComparisonDetailView(FeatureAPIView):
    name = "Comparison Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "housing_scenario_views",
            "comparison_detail",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, comparison_id):
        from .housing_scenario_models import HousingScenarioComparison

        row = get_object_or_404(HousingScenarioComparison, id=comparison_id)
        access.scenario_for(request.user, row.scenario.id)
        for item in row.snapshot["scenarios"]:
            access.scenario_for(request.user, item["scenario_id"])
        return Response({"id": str(row.id), "revision": row.revision, **row.snapshot})


# Stable callable import for integrations; URLs use the explicit class.
comparison_detail = ComparisonDetailView.as_view()


class ScenariosView(FeatureAPIView):
    name = "Scenarios"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "housing_scenario_views",
            "scenarios",
            boundary="planning",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "housing_scenario_views",
            "scenarios",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id):
        company = access.company_for(
            request.user, company_id, write=request.method == "POST"
        )
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

    def post(self, request, company_id):
        access.company_for(request.user, company_id, write=request.method == "POST")
        require_planning(request.user, CAPABILITY)
        return mutate(
            request,
            "housing_scenario.create",
            lambda: access.company_for(request.user, company_id, write=True, lock=True),
            lambda item, _: commands.create(request.user, item, request.data),
            lambda item: projections.payload(item, request.user),
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
scenarios = ScenariosView.as_view()


class ScenarioDetailView(FeatureAPIView):
    name = "Scenario Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "housing_scenario_views",
            "scenario_detail",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, scenario_id):
        return Response(
            projections.payload(
                access.scenario_for(request.user, scenario_id), request.user
            )
        )


# Stable callable import for integrations; URLs use the explicit class.
scenario_detail = ScenarioDetailView.as_view()


class ScenarioActionView(FeatureAPIView):
    name = "Scenario Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "housing_scenario_views",
            "scenario_action",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, scenario_id, action):
        require_planning(request.user, CAPABILITY)
        if action not in {
            "runs",
            "duplicate",
            "request-decision",
            "compare",
            "validate",
        }:
            raise ValidationError({"action": "Choose a supported decision action."})
        return mutate(
            request,
            "housing_scenario." + action,
            lambda: access.scenario_for(
                request.user, scenario_id, write=True, lock=True
            ),
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


# Stable callable import for integrations; URLs use the explicit class.
scenario_action = ScenarioActionView.as_view()


class ScenarioRunView(FeatureAPIView):
    name = "Scenario Run"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "housing_scenario_views",
            "scenario_run",
            boundary="planning",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "housing_scenario_views",
            "scenario_run",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, run_id):
        load = partial(
            entry_commands.scenario_run_get_load, actor=request.user, run_id=run_id
        )
        return Response(projections.run_payload(load(), request.user))

    def post(self, request, run_id):
        load = partial(
            entry_commands.scenario_run_post_load, actor=request.user, run_id=run_id
        )
        require_planning(request.user, CAPABILITY)
        return mutate(
            request,
            "housing_scenario.cancel",
            load,
            lambda run, _: jobs.cancel(request.user, run),
            lambda run: projections.run_payload(run, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
scenario_run = ScenarioRunView.as_view()


class ScenarioDecisionView(FeatureAPIView):
    name = "Scenario Decision"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "housing_scenario_views",
            "scenario_decision",
            boundary="planning",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "housing_scenario_views",
            "scenario_decision",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, decision_id, action=""):
        return Response(
            decisions.payload(
                decisions.for_user(request.user, decision_id), request.user
            )
        )

    def post(self, request, decision_id, action=""):
        require_planning(request.user, CAPABILITY)
        if action not in {"decide", "prepare-booking", "execute"}:
            raise ValidationError({"action": "Choose a supported decision action."})
        apply = partial(
            entry_commands.scenario_decision_post_apply,
            action=action,
            actor=request.user,
            receipt_data=request.data,
        )
        serialize = partial(
            entry_commands.scenario_decision_post_serialize,
            action=action,
            actor=request.user,
        )
        return mutate(
            request,
            "housing_decision." + action,
            lambda: decisions.for_user(request.user, decision_id, lock=True),
            apply,
            serialize,
        )


# Stable callable import for integrations; URLs use the explicit class.
scenario_decision = ScenarioDecisionView.as_view()


class ScenarioSourcesView(FeatureAPIView):
    name = "Scenario Sources"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "housing_scenario_views",
            "scenario_sources",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, company_id, kind):
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
                    "status": (
                        "active_member" if row.membership_id else "prepared_staff"
                    ),
                },
            )
        if kind == "offers":
            context = access.request_for(
                request.user, request.query_params.get("request_id"), write=True
            )
            if context.company_id != company.pk:
                raise ValidationError(
                    {"request_id": "Choose a request from this company."}
                )

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


# Stable callable import for integrations; URLs use the explicit class.
scenario_sources = ScenarioSourcesView.as_view()
