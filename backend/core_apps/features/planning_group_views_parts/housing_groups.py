"""Planning group views: housing groups."""

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer


from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from ..planning_models import GroupMembership, HousingGroup
from ..services.planning import mutate, page
from .process_payload import group_for, _group_values
from .group_payload import group_payload


class HousingGroupsView(FeatureAPIView):
    name = "Housing Groups"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "housing_groups",
            "housing_groups",
            boundary="planning",
            capability="housing_groups",
            typed=False,
        ),
        "post": ActionPolicy(
            "housing_groups",
            "housing_groups",
            boundary="planning",
            capability="housing_groups",
            typed=False,
        ),
    }

    def get(self, request):
        groups = HousingGroup.objects.filter(
            memberships__user=request.user, memberships__status="active"
        )
        status = request.query_params.get("status")
        if status:
            if status not in {"active", "archived"}:
                raise ValidationError({"status": "Choose active or archived."})
            groups = groups.filter(status=status)
        return page(
            request,
            groups.order_by("-created_at", "pkid"),
            lambda x: group_payload(x, request.user),
        )

    def post(self, request):
        def apply(_, revision):
            if (
                request.data.get("action") != "create"
                or request.data.get("roster_revision") != 0
            ):
                raise ValidationError(
                    "New groups use action=create and roster_revision=0."
                )
            group = HousingGroup.objects.create(**_group_values(request.data))
            GroupMembership.objects.create(group=group, user=request.user, role="admin")
            from core_apps.chat.services.group_provisioning import provision_group

            provision_group(group)
            return group

        return mutate(
            request,
            "group.create",
            lambda: None,
            apply,
            lambda x: group_payload(x, request.user),
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
housing_groups = HousingGroupsView.as_view()


class HousingGroupDetailView(FeatureAPIView):
    name = "Housing Group Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "housing_groups",
            "housing_group_detail",
            boundary="planning",
            capability="housing_groups",
            typed=False,
        ),
    }

    def get(self, request, group_id):
        return Response(group_payload(group_for(request.user, group_id), request.user))


# Stable callable import for integrations; URLs use the explicit class.
housing_group_detail = HousingGroupDetailView.as_view()
