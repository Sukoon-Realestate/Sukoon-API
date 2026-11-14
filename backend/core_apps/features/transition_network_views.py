from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .services.planning import mutate, page, require_planning
from .transition_network_models import (
    MoveIntent,
    TransitionCandidate,
    TransitionMatchRun,
)
from .planning_models import TenancyTransition
from .services.transition_network import access, commands, projections

CAPABILITY = "housing_transition_planning"


class ContextView(FeatureAPIView):
    name = "Context"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "transition_network_views",
            "context",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, lease_id):
        lease = commands.own_lease(request.user, lease_id)
        sources = TenancyTransition.objects.filter(
            lease=lease, kind="replacement"
        ).exclude(status__in=["withdrawn", "declined", "cancelled", "expired"])
        return Response(
            {
                "lease_id": str(lease.id),
                "end_on": str(lease.end_date),
                "city": {
                    "id": str(lease.property.city.id),
                    "name": lease.property.city.name,
                },
                "source_transitions": [
                    {
                        "id": str(item.id),
                        "requested_on": str(item.requested_on),
                        "availability_approved": item.availability_approved,
                    }
                    for item in sources
                ],
                "execution_available": projections.execution_enabled(),
            }
        )


# Stable callable import for integrations; URLs use the explicit class.
context = ContextView.as_view()


class IntentsView(FeatureAPIView):
    name = "Intents"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "transition_network_views",
            "intents",
            boundary="planning",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "transition_network_views",
            "intents",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        rows = MoveIntent.objects.filter(user=request.user).select_related(
            "lease", "source_transition"
        )
        if request.query_params.get("lease_id"):
            rows = rows.filter(lease__id=request.query_params["lease_id"])
        return page(request, rows, projections.intent_payload)

    def post(self, request):
        require_planning(request.user, CAPABILITY)
        return mutate(
            request,
            "move_intent.create",
            lambda: commands.own_lease(
                request.user, request.data.get("lease_id"), lock=True
            ),
            lambda _, revision: commands.create(request),
            projections.intent_payload,
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
intents = IntentsView.as_view()


class IntentDetailView(FeatureAPIView):
    name = "Intent Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "transition_network_views",
            "intent_detail",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, intent_id):
        return Response(
            projections.intent_payload(access.intent_for(request.user, intent_id))
        )


# Stable callable import for integrations; URLs use the explicit class.
intent_detail = IntentDetailView.as_view()


class IntentActionView(FeatureAPIView):
    name = "Intent Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "transition_network_views",
            "intent_action",
            boundary="planning",
            capability=CAPABILITY,
            typed=False,
        ),
    }

    def post(self, request, intent_id, action):
        if action not in {"update", "publish", "pause", "withdraw", "match-runs"}:
            raise ValidationError({"action": "Unsupported move action."})
        action = "match" if action == "match-runs" else action
        return mutate(
            request,
            f"move_intent.{action}.{intent_id}",
            lambda: access.intent_for(request.user, intent_id, lock=True),
            lambda item, revision: commands.change(request, item, action),
            (
                projections.run_payload
                if action == "match"
                else projections.intent_payload
            ),
        )


# Stable callable import for integrations; URLs use the explicit class.
intent_action = IntentActionView.as_view()


class RunsView(FeatureAPIView):
    name = "Runs"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "transition_network_views",
            "runs",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, intent_id):
        item = access.intent_for(request.user, intent_id)
        return page(request, item.runs.order_by("-created_at"), projections.run_payload)


# Stable callable import for integrations; URLs use the explicit class.
runs = RunsView.as_view()


class RunDetailView(FeatureAPIView):
    name = "Run Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "transition_network_views",
            "run_detail",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, run_id):
        item = get_object_or_404(TransitionMatchRun, id=run_id, user=request.user)
        return Response(projections.run_payload(item))


# Stable callable import for integrations; URLs use the explicit class.
run_detail = RunDetailView.as_view()


class CandidatesView(FeatureAPIView):
    name = "Candidates"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "transition_network_views",
            "candidates",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        rows = (
            TransitionCandidate.objects.filter(participants__user=request.user)
            .distinct()
            .order_by("-created_at")
        )
        if request.query_params.get("run_id"):
            rows = rows.filter(run__id=request.query_params["run_id"])
        return page(
            request,
            rows,
            lambda item: projections.candidate_payload(item, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
candidates = CandidatesView.as_view()


class CandidateDetailView(FeatureAPIView):
    name = "Candidate Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "transition_network_views",
            "candidate_detail",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, candidate_id):
        return Response(
            projections.candidate_payload(
                access.candidate_for(request.user, candidate_id), request.user
            )
        )


# Stable callable import for integrations; URLs use the explicit class.
candidate_detail = CandidateDetailView.as_view()


class CandidateInterestView(FeatureAPIView):
    name = "Candidate Interest"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "transition_network_views",
            "candidate_interest",
            boundary="planning",
            capability=CAPABILITY,
            typed=False,
        ),
    }

    def post(self, request, candidate_id):
        return mutate(
            request,
            f"transition.interest.{candidate_id}",
            lambda: access.candidate_for(request.user, candidate_id, lock=True),
            lambda item, revision: commands.respond(request, item),
            lambda item: projections.candidate_payload(item, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
candidate_interest = CandidateInterestView.as_view()


class PrepareView(FeatureAPIView):
    name = "Prepare"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "transition_network_views",
            "prepare",
            boundary="planning",
            capability="housing_transition_execution",
            typed=False,
        ),
    }

    def post(self, request, candidate_id):
        from .services.transition_network.execution import create
        from .services.advanced_execution.projections import payload

        return mutate(
            request,
            f"transition.execution.{candidate_id}",
            lambda: access.candidate_for(request.user, candidate_id, lock=True),
            lambda item, revision: create(request, item),
            lambda item: payload(item, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
prepare = PrepareView.as_view()
