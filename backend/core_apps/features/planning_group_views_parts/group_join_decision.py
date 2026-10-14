"""Planning group views: group join decision."""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from ..planning_models import (
    GroupJoinRequest,
    GroupMembership,
    GroupProcess,
    HousingGroup,
)
from ..services.planning import (
    check_revision,
    mutate,
    page,
    planning_api,
    selection,
    text_field,
)
from ..services.rental_phase2 import RentalConflict
from .process_payload import active_ids, process_payload, invalidate_roster
from .group_payload import join_payload


@planning_api(["POST"], "housing_groups")
def group_join_decision(request, join_id, action):
    def load():
        item = get_object_or_404(GroupJoinRequest, id=join_id)
        HousingGroup.objects.select_for_update().get(pk=item.group_id)
        return GroupJoinRequest.objects.select_for_update().get(pk=item.pk)

    def apply(item, revision):
        if action not in join_payload(item, request.user)["allowed_actions"] or (
            action == "withdraw" and item.user_id != request.user.pk
        ):
            raise PermissionDenied()
        group = item.group
        if action == "approve":
            if group.status != "active" or group.visibility != "open":
                raise RentalConflict("This group no longer accepts join requests.")
            if not item.user.is_active or not item.user.is_verified:
                raise RentalConflict("The applicant is no longer eligible.")
            if len(active_ids(group)) >= group.capacity:
                raise RentalConflict("The group is full.", code="group_full")
            if group.memberships.filter(
                user=item.user, status__in=["active", "removed"]
            ).exists():
                raise RentalConflict("Membership changed; refresh this request.")
            GroupMembership.objects.update_or_create(
                group=group,
                user=item.user,
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
            roster_changed(group, actor=request.user, kind="member_joined", subject=item.user)
        item.status = {
            "approve": "approved",
            "decline": "declined",
            "withdraw": "withdrawn",
        }[action]
        item.revision += 1
        item.save()
        return item

    return mutate(
        request,
        f"group.join.{action}.{join_id}",
        load,
        apply,
        lambda x: join_payload(x, request.user),
    )


def owner_application_payload(item):
    return {
        **process_payload(item, item.property.owner),
        "group_id": str(item.group.id),
        "group_name": item.group.name,
        "owner_note": item.owner_note,
        "allowed_actions": (
            ["approve", "decline", "request_changes"]
            if item.status == "under_review"
            else []
        ),
    }


@planning_api(["GET"], "group_applications")
def owner_group_applications(request):
    items = (
        GroupProcess.objects.filter(kind="application", property__owner=request.user)
        .exclude(status__in=["collecting_consent", "ready"])
        .select_related("property__owner", "group", "interest", "visit")
        .order_by("-created_at", "pkid")
    )
    return page(request, items, owner_application_payload)


@planning_api(["GET"], "group_applications")
def owner_group_application_detail(request, application_id):
    item = get_object_or_404(
        GroupProcess,
        id=application_id,
        kind="application",
        property__owner=request.user,
    )
    if item.status in {"collecting_consent", "ready"}:
        raise NotFound()
    return Response(owner_application_payload(item))


@planning_api(["POST"], "group_applications")
def owner_group_application_action(request, application_id, action):
    def load():
        item = get_object_or_404(
            GroupProcess,
            id=application_id,
            kind="application",
            property__owner=request.user,
        )
        HousingGroup.objects.select_for_update().get(pk=item.group_id)
        return GroupProcess.objects.select_for_update().get(pk=item.pk)

    def apply(item, revision):
        if action not in owner_application_payload(item)["allowed_actions"]:
            raise PermissionDenied()
        check_revision(item.group.roster_revision, item.roster_revision)
        selection(request, item.selection, owned=True)
        if set(item.participant_ids) != set(item.consented_ids):
            raise RentalConflict("Every applicant must approve the current proposal.")
        item.status = {
            "approve": "approved_to_proceed",
            "decline": "rejected",
            "request_changes": "changes_requested",
        }[action]
        item.owner_note = text_field(
            request.data, "note", required=action == "request_changes"
        )
        item.revision += 1
        item.history.append(
            {
                "action": action,
                "at": timezone.now().isoformat(),
                "revision": item.revision,
            }
        )
        item.save()
        return item

    return mutate(
        request,
        f"group.application.{action}.{application_id}",
        load,
        apply,
        owner_application_payload,
    )
