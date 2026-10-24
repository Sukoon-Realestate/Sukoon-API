from django.db.models import Q
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .services.planning import (
    planning_api,
    mutate,
    page,
    require_planning,
    eligible_owner,
)
from .shared_housing_models import SharedHousingPlan
from .services.shared_housing import commands
from .services.shared_housing.access import CAPABILITY, get_plan, visible
from .services.shared_housing.projections import payload


@transaction.atomic
def shared_mutate(
    request, operation, load, apply, serialize, *, creating=False, plan_id=None
):
    from core_apps.users.models import User
    from .planning_models import RoommateConnection

    if creating:
        connection = get_object_or_404(
            RoommateConnection.objects.filter(
                Q(first=request.user) | Q(second=request.user)
            ),
            id=request.data.get("connection_id"),
        )
    else:
        connection = get_plan(request.user, plan_id).connection
    # Acquire both participant roots before mutate's actor lock and the connection.
    # Otherwise crossed creation deadlocks when moderation upgrades the peer lock.
    list(
        User.objects.select_for_update(no_key=True)
        .filter(pk__in={connection.first_id, connection.second_id, request.user.pk})
        .order_by("pk")
    )
    return mutate(request, operation, load, apply, serialize, creating=creating)


@planning_api(["GET", "POST"], None, typed=True)
def plans(request):
    if request.method == "GET":
        query = visible(request.user).filter(
            Q(connection__first=request.user) | Q(connection__second=request.user)
        )
        return page(
            request,
            query.order_by("-created_at", "pkid"),
            lambda value: payload(value, request.user),
        )
    require_planning(request.user, CAPABILITY)
    return shared_mutate(
        request,
        "shared.create",
        lambda: None,
        lambda *_: commands.create(request),
        lambda value: payload(value, request.user),
        creating=True,
    )


@planning_api(["GET"], None)
def detail(request, plan_id):
    return Response(payload(get_plan(request.user, plan_id), request.user))


@planning_api(["POST"], None, typed=True)
def action(request, plan_id, action):
    if action not in {"withdraw", "decline_invite", "unpublish"}:
        require_planning(request.user, CAPABILITY)
    return shared_mutate(
        request,
        f"shared.{action}.{plan_id}",
        lambda: get_plan(request.user, plan_id, lock=True),
        lambda plan, _: commands.plan_action(request, plan, action),
        lambda value: payload(value, request.user),
        plan_id=plan_id,
    )


@planning_api(["GET", "POST"], None, typed=True)
def proposals(request, plan_id):
    if request.method == "GET":
        return Response(payload(get_plan(request.user, plan_id), request.user))
    require_planning(request.user, CAPABILITY)
    return shared_mutate(
        request,
        f"shared.propose.{plan_id}",
        lambda: get_plan(request.user, plan_id, lock=True),
        lambda plan, _: commands.propose(request, plan),
        lambda value: payload(value, request.user),
        plan_id=plan_id,
    )


@planning_api(["POST"], None, typed=True)
def proposal_action(request, plan_id, proposal_id, action):
    require_planning(request.user, CAPABILITY)
    return shared_mutate(
        request,
        f"shared.proposal.{action}.{proposal_id}",
        lambda: get_plan(request.user, plan_id, lock=True),
        lambda plan, _: commands.proposal_action(request, plan, proposal_id, action),
        lambda value: payload(value, request.user),
        plan_id=plan_id,
    )


@planning_api(["GET"], CAPABILITY)
def demand(request):
    if not eligible_owner(request.user):
        raise PermissionDenied("Verified listing ownership is required.")
    query = SharedHousingPlan.objects.filter(
        published=True,
        status="searching",
        expires_at__gt=timezone.now(),
        connection__status="accepted",
    ).exclude(Q(connection__first=request.user) | Q(connection__second=request.user))
    return page(
        request,
        query.order_by("-created_at", "pkid"),
        lambda value: payload(value, request.user),
    )


@planning_api(["GET"], None)
def applications(request):
    query = (
        visible(request.user).filter(proposals__property__owner=request.user).distinct()
    )
    return page(
        request,
        query.order_by("-created_at", "pkid"),
        lambda value: payload(value, request.user),
    )
