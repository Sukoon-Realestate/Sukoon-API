from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .services.planning import planning_api, mutate, page, require_planning
from .services.rental_phase2 import RentalConflict
from .transition_network_models import (
    MoveIntent,
    TransitionCandidate,
    TransitionMatchRun,
)
from .planning_models import TenancyTransition
from .services.transition_network import access, commands, projections

CAPABILITY = "housing_transition_planning"


@planning_api(["GET"], None)
def context(request, lease_id):
    lease = commands.own_lease(request.user, lease_id)
    sources = TenancyTransition.objects.filter(lease=lease, kind="replacement").exclude(
        status__in=["withdrawn", "declined", "cancelled", "expired"]
    )
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


@planning_api(["GET", "POST"], None)
def intents(request):
    if request.method == "GET":
        rows = MoveIntent.objects.filter(user=request.user).select_related(
            "lease", "source_transition"
        )
        if request.query_params.get("lease_id"):
            rows = rows.filter(lease__id=request.query_params["lease_id"])
        return page(request, rows, projections.intent_payload)
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


@planning_api(["GET"], None)
def intent_detail(request, intent_id):
    return Response(
        projections.intent_payload(access.intent_for(request.user, intent_id))
    )


@planning_api(["POST"], CAPABILITY)
def intent_action(request, intent_id, action):
    if action not in {"update", "publish", "pause", "withdraw", "match-runs"}:
        raise ValidationError({"action": "Unsupported move action."})
    action = "match" if action == "match-runs" else action
    return mutate(
        request,
        f"move_intent.{action}.{intent_id}",
        lambda: access.intent_for(request.user, intent_id, lock=True),
        lambda item, revision: commands.change(request, item, action),
        projections.run_payload if action == "match" else projections.intent_payload,
    )


@planning_api(["GET"], None)
def runs(request, intent_id):
    item = access.intent_for(request.user, intent_id)
    return page(request, item.runs.order_by("-created_at"), projections.run_payload)


@planning_api(["GET"], None)
def run_detail(request, run_id):
    item = get_object_or_404(TransitionMatchRun, id=run_id, user=request.user)
    return Response(projections.run_payload(item))


@planning_api(["GET"], None)
def candidates(request):
    rows = (
        TransitionCandidate.objects.filter(participants__user=request.user)
        .distinct()
        .order_by("-created_at")
    )
    if request.query_params.get("run_id"):
        rows = rows.filter(run__id=request.query_params["run_id"])
    return page(
        request, rows, lambda item: projections.candidate_payload(item, request.user)
    )


@planning_api(["GET"], None)
def candidate_detail(request, candidate_id):
    return Response(
        projections.candidate_payload(
            access.candidate_for(request.user, candidate_id), request.user
        )
    )


@planning_api(["POST"], CAPABILITY)
def candidate_interest(request, candidate_id):
    return mutate(
        request,
        f"transition.interest.{candidate_id}",
        lambda: access.candidate_for(request.user, candidate_id, lock=True),
        lambda item, revision: commands.respond(request, item),
        lambda item: projections.candidate_payload(item, request.user),
    )


@planning_api(["POST"], "housing_transition_execution")
def prepare(request, candidate_id):
    from .services.transition_network.execution import create
    from .services.advanced_execution.projections import payload

    return mutate(
        request,
        f"transition.execution.{candidate_id}",
        lambda: access.candidate_for(request.user, candidate_id, lock=True),
        lambda item, revision: create(request, item),
        lambda item: payload(item, request.user),
    )
