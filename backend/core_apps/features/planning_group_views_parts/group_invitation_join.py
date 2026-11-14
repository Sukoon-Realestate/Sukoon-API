"""Planning group views: group invitation join."""

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer


from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from ..planning_models import GroupJoinRequest, GroupMembership, HousingGroup
from ..services.planning import (
    check_revision,
    criteria_payload,
    mutate,
    page,
    text_field,
)
from ..services.rental_phase2 import RentalConflict
from .process_payload import active_ids, invalidate_roster
from .invitation_from_token import invitation_from_token
from .group_payload import group_payload, join_payload


class GroupInvitationJoinView(FeatureAPIView):
    name = "Group Invitation Join"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "group_invitation_join",
            "group_invitation_join",
            boundary="planning",
            capability="housing_groups",
            typed=False,
        ),
    }

    def post(self, request):
        def load():
            invite = invitation_from_token(request.data.get("token"))
            return HousingGroup.objects.select_for_update().get(pk=invite.group_id)

        def apply(group, revision):
            invitation_from_token(
                request.data.get("token")
            )  # Recheck revocation after lock.
            if str(request.data.get("group_id")) != str(group.id):
                raise ValidationError({"group_id": "Invitation group mismatch."})
            check_revision(group.revision, request.data.get("group_revision"))
            if group.memberships.filter(user=request.user, status="active").exists():
                raise RentalConflict("You are already a member.")
            if group.memberships.filter(user=request.user, status="removed").exists():
                raise PermissionDenied(
                    "Removed members cannot reuse an old invitation."
                )
            if len(active_ids(group)) >= group.capacity:
                raise RentalConflict("The group is full.", code="group_full")
            GroupMembership.objects.update_or_create(
                group=group,
                user=request.user,
                defaults={
                    "role": "member",
                    "status": "active",
                    "joined_revision": group.revision + 1,
                },
            )
            invalidate_roster(group)
            group.revision += 1
            group.save()
            from core_apps.chat.services.group_provisioning import roster_changed

            roster_changed(
                group, actor=request.user, kind="member_joined", subject=request.user
            )
            return group

        return mutate(
            request, "group.join", load, apply, lambda x: group_payload(x, request.user)
        )


# Stable callable import for integrations; URLs use the explicit class.
group_invitation_join = GroupInvitationJoinView.as_view()


class OpenGroupsView(FeatureAPIView):
    name = "Open Groups"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "group_invitation_join",
            "open_groups",
            boundary="planning",
            capability="housing_groups",
            typed=False,
        ),
    }

    def get(self, request):
        groups = (
            HousingGroup.objects.filter(status="active", visibility="open")
            .exclude(memberships__user=request.user, memberships__status="removed")
            .order_by("-created_at", "pkid")
        )
        return page(
            request,
            groups,
            lambda x: {
                "id": str(x.id),
                "name": x.name,
                "revision": x.revision,
                "capacity": x.capacity,
                "member_count": x.memberships.filter(status="active").count(),
                "criteria": criteria_payload(x.criteria),
                "status": x.status,
            },
        )


# Stable callable import for integrations; URLs use the explicit class.
open_groups = OpenGroupsView.as_view()


class GroupJoinRequestView(FeatureAPIView):
    name = "Group Join Request"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "group_invitation_join",
            "group_join_request",
            boundary="planning",
            capability="housing_groups",
            typed=False,
        ),
    }

    def post(self, request, group_id):
        def apply(group, revision):
            check_revision(group.revision, request.data.get("group_revision"))
            if group.visibility != "open" or group.status != "active":
                raise NotFound()
            if group.memberships.filter(
                user=request.user, status__in=["active", "removed"]
            ).exists():
                raise PermissionDenied("Membership does not permit a new join request.")
            if len(active_ids(group)) >= group.capacity:
                raise RentalConflict("The group is full.", code="group_full")
            if group.join_requests.filter(user=request.user, status="pending").exists():
                raise RentalConflict("A join request is already pending.")
            item, created = GroupJoinRequest.objects.get_or_create(
                group=group, user=request.user
            )
            item.status, item.note = "pending", text_field(request.data, "note")
            if not created:
                item.revision += 1
            item.save()
            return item

        return mutate(
            request,
            f"group.join_request.{group_id}",
            lambda: get_object_or_404(
                HousingGroup.objects.select_for_update(), id=group_id
            ),
            apply,
            lambda x: join_payload(x, request.user),
            creating=True,
        )


# Stable callable import for integrations; URLs use the explicit class.
group_join_request = GroupJoinRequestView.as_view()


class GroupJoinDetailView(FeatureAPIView):
    name = "Group Join Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "group_invitation_join",
            "group_join_detail",
            boundary="planning",
            capability="housing_groups",
            typed=False,
        ),
    }

    def get(self, request, join_id):
        item = get_object_or_404(
            GroupJoinRequest.objects.select_related("group", "user"), id=join_id
        )
        if (
            item.user_id != request.user.pk
            and not item.group.memberships.filter(
                user=request.user, role="admin", status="active"
            ).exists()
        ):
            raise NotFound()
        return Response(join_payload(item, request.user))


# Stable callable import for integrations; URLs use the explicit class.
group_join_detail = GroupJoinDetailView.as_view()


class MyGroupJoinRequestsView(FeatureAPIView):
    name = "My Group Join Requests"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "group_invitation_join",
            "my_group_join_requests",
            boundary="planning",
            capability="housing_groups",
            typed=False,
        ),
    }

    def get(self, request):
        return page(
            request,
            GroupJoinRequest.objects.filter(user=request.user)
            .select_related("group", "user")
            .order_by("-created_at", "pkid"),
            lambda x: join_payload(x, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
my_group_join_requests = MyGroupJoinRequestsView.as_view()
