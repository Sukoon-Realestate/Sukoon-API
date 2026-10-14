"""Planning group views: housing groups."""

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from ..planning_models import GroupMembership, HousingGroup
from ..services.planning import mutate, page, planning_api
from .process_payload import group_for, _group_values
from .group_payload import group_payload


@planning_api(["GET", "POST"], "housing_groups")
def housing_groups(request):
    if request.method == "GET":
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

    def apply(_, revision):
        if (
            request.data.get("action") != "create"
            or request.data.get("roster_revision") != 0
        ):
            raise ValidationError("New groups use action=create and roster_revision=0.")
        group = HousingGroup.objects.create(**_group_values(request.data))
        GroupMembership.objects.create(group=group, user=request.user, role="admin")
        return group

    return mutate(
        request,
        "group.create",
        lambda: None,
        apply,
        lambda x: group_payload(x, request.user),
        creating=True,
    )


@planning_api(["GET"], "housing_groups")
def housing_group_detail(request, group_id):
    return Response(group_payload(group_for(request.user, group_id), request.user))
