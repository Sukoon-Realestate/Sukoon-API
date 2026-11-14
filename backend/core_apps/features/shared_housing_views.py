from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from django.db.models import Q
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .services.planning import mutate, page, require_planning, eligible_owner
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


class PlansView(FeatureAPIView):
    name = "Plans"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "shared_housing_views",
            "plans",
            boundary="planning",
            capability=None,
            typed=True,
        ),
        "post": ActionPolicy(
            "shared_housing_views",
            "plans",
            boundary="planning",
            capability=None,
            typed=True,
        ),
    }

    def get(self, request):
        query = visible(request.user).filter(
            Q(connection__first=request.user) | Q(connection__second=request.user)
        )
        return page(
            request,
            query.order_by("-created_at", "pkid"),
            lambda value: payload(value, request.user),
        )

    def post(self, request):
        require_planning(request.user, CAPABILITY)
        return shared_mutate(
            request,
            "shared.create",
            lambda: None,
            lambda *_: commands.create(request),
            lambda value: payload(value, request.user),
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
plans = PlansView.as_view()


class DetailView(FeatureAPIView):
    name = "Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "shared_housing_views",
            "detail",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, plan_id):
        return Response(payload(get_plan(request.user, plan_id), request.user))


# Stable callable import for integrations; URLs use the explicit class.
detail = DetailView.as_view()


class ActionView(FeatureAPIView):
    name = "Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "shared_housing_views",
            "action",
            boundary="planning",
            capability=None,
            typed=True,
        ),
    }

    def post(self, request, plan_id, action):
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


# Stable callable import for integrations; URLs use the explicit class.
action = ActionView.as_view()


class ProposalsView(FeatureAPIView):
    name = "Proposals"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "shared_housing_views",
            "proposals",
            boundary="planning",
            capability=None,
            typed=True,
        ),
        "post": ActionPolicy(
            "shared_housing_views",
            "proposals",
            boundary="planning",
            capability=None,
            typed=True,
        ),
    }

    def get(self, request, plan_id):
        return Response(payload(get_plan(request.user, plan_id), request.user))

    def post(self, request, plan_id):
        require_planning(request.user, CAPABILITY)
        return shared_mutate(
            request,
            f"shared.propose.{plan_id}",
            lambda: get_plan(request.user, plan_id, lock=True),
            lambda plan, _: commands.propose(request, plan),
            lambda value: payload(value, request.user),
            plan_id=plan_id,
        )


# Stable callable import for integrations; URLs use the explicit class.
proposals = ProposalsView.as_view()


class ProposalActionView(FeatureAPIView):
    name = "Proposal Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "shared_housing_views",
            "proposal_action",
            boundary="planning",
            capability=None,
            typed=True,
        ),
    }

    def post(self, request, plan_id, proposal_id, action):
        require_planning(request.user, CAPABILITY)
        return shared_mutate(
            request,
            f"shared.proposal.{action}.{proposal_id}",
            lambda: get_plan(request.user, plan_id, lock=True),
            lambda plan, _: commands.proposal_action(
                request, plan, proposal_id, action
            ),
            lambda value: payload(value, request.user),
            plan_id=plan_id,
        )


# Stable callable import for integrations; URLs use the explicit class.
proposal_action = ProposalActionView.as_view()


class DemandView(FeatureAPIView):
    name = "Demand"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "shared_housing_views",
            "demand",
            boundary="planning",
            capability=CAPABILITY,
            typed=False,
        ),
    }

    def get(self, request):
        if not eligible_owner(request.user):
            raise PermissionDenied("Verified listing ownership is required.")
        query = SharedHousingPlan.objects.filter(
            published=True,
            status="searching",
            expires_at__gt=timezone.now(),
            connection__status="accepted",
        ).exclude(
            Q(connection__first=request.user) | Q(connection__second=request.user)
        )
        return page(
            request,
            query.order_by("-created_at", "pkid"),
            lambda value: payload(value, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
demand = DemandView.as_view()


class ApplicationsView(FeatureAPIView):
    name = "Applications"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "shared_housing_views",
            "applications",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        query = (
            visible(request.user)
            .filter(proposals__property__owner=request.user)
            .distinct()
        )
        return page(
            request,
            query.order_by("-created_at", "pkid"),
            lambda value: payload(value, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
applications = ApplicationsView.as_view()
