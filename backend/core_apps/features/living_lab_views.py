from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from rest_framework.response import Response

from .living_lab_models import LivingLabAuditEvent, SharedLivingLab
from .services.living_lab.access import CAPABILITY, group_for, lab_for
from .services.living_lab.commands import change, create
from .services.living_lab.projections import lab_payload, private_payload
from .services.planning import mutate, page, require_planning


class LivingLabsView(FeatureAPIView):
    name = "Living Labs"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "living_lab_views",
            "living_labs",
            boundary="planning",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "living_lab_views",
            "living_labs",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, group_id):
        group = group_for(request.user, group_id)
        member = group.memberships.get(user=request.user, status="active")
        labs = SharedLivingLab.objects.filter(
            group=group,
            access_group_revision__gte=member.joined_revision,
        ).order_by("-created_at", "pkid")
        return page(
            request, labs, lambda row: lab_payload(row, request.user, detail=False)
        )

    def post(self, request, group_id):
        group_for(request.user, group_id)
        require_planning(request.user, CAPABILITY)
        return mutate(
            request,
            f"living_lab.create:{group_id}",
            lambda: group_for(request.user, group_id, lock=True, coordinator=True),
            lambda group, _: create(request, group),
            lambda lab: lab_payload(lab, request.user),
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
living_labs = LivingLabsView.as_view()


class LivingLabDetailView(FeatureAPIView):
    name = "Living Lab Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "living_lab_views",
            "living_lab_detail",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, lab_id):
        lab = lab_for(request.user, lab_id)
        LivingLabAuditEvent.objects.create(lab=lab, actor=request.user, event="read")
        return Response(lab_payload(lab, request.user))


# Stable callable import for integrations; URLs use the explicit class.
living_lab_detail = LivingLabDetailView.as_view()


class LivingLabRequirementsView(FeatureAPIView):
    name = "Living Lab Requirements"
    http_method_names = ["get", "post", "put", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "living_lab_views",
            "living_lab_requirements",
            boundary="planning",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "living_lab_views",
            "living_lab_requirements",
            boundary="planning",
            capability=None,
            typed=False,
        ),
        "put": ActionPolicy(
            "living_lab_views",
            "living_lab_requirements",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, lab_id):
        lab = lab_for(request.user, lab_id)
        LivingLabAuditEvent.objects.create(
            lab=lab, actor=request.user, event="read_own_requirements"
        )
        return Response(private_payload(lab, request.user))

    def post(self, request, lab_id):
        lab_for(request.user, lab_id)
        require_planning(request.user, CAPABILITY)
        return mutate(
            request,
            f"living_lab.requirements:{lab_id}",
            lambda: lab_for(request.user, lab_id, lock=True),
            lambda lab, _: change(request, lab, "requirements"),
            lambda lab: lab_payload(lab, request.user),
        )

    def put(self, request, lab_id):
        lab_for(request.user, lab_id)
        require_planning(request.user, CAPABILITY)
        return mutate(
            request,
            f"living_lab.requirements:{lab_id}",
            lambda: lab_for(request.user, lab_id, lock=True),
            lambda lab, _: change(request, lab, "requirements"),
            lambda lab: lab_payload(lab, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
living_lab_requirements = LivingLabRequirementsView.as_view()


class LivingLabActionView(FeatureAPIView):
    name = "Living Lab Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "living_lab_views",
            "living_lab_action",
            boundary="planning",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, lab_id, action):
        if action != "withdraw":
            require_planning(request.user, CAPABILITY)
        lab = lab_for(request.user, lab_id)
        if action in {"run", "scenario"}:
            # Record authorized attempts, including rejected limits and identical retries, without private values.
            LivingLabAuditEvent.objects.create(
                lab=lab, actor=request.user, event=f"{action}_attempt"
            )
        return mutate(
            request,
            f"living_lab.{action}:{lab_id}",
            lambda: lab_for(request.user, lab_id, lock=True),
            lambda lab, _: _apply_action(request, lab, action),
            lambda lab: lab_payload(lab, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
living_lab_action = LivingLabActionView.as_view()


def _apply_action(request, lab, action):
    if action == "scenario":
        from .services.living_lab.journeys import child_lab

        return child_lab(request, lab)
    return change(request, lab, action)
