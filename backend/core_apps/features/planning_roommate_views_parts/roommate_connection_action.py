"""Planning roommate views: roommate connection action."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..services.planning import mutate, planning_api
from ..services.lifestyle_matching import disclosure_scope
from .profile_values import DIMENSIONS, connections, roommate_actions
from .roommate_candidate_action import connection_payload


@planning_api(["POST"], "roommates")
def roommate_connection_action(request, connection_id, action):
    def apply(item, revision):
        if action not in roommate_actions(request.user, item):
            raise PermissionDenied("This connection action is not available to you.")
        if request.data.get("decision") != action:
            raise ValidationError({"decision": "Must match the route."})
        item.status = {
            "accept": "accepted",
            "decline": "declined",
            "withdraw": "withdrawn",
            "block": "blocked",
        }[action]
        if action == "block":
            item.blocked_by = [str(request.user.id)]
        if action == "accept":
            item.disclosure_grants[str(request.user.id)] = disclosure_scope(
                request.user, request.data, DIMENSIONS
            )
        elif action in {"withdraw", "block", "decline"}:
            item.disclosure_grants = {}
        item.revision += 1
        item.save()
        if action != "accept":
            from ..services.shared_housing.commands import connection_closed
            connection_closed(item, request.user)
        return item

    return mutate(
        request,
        f"roommate.connection.{action}.{connection_id}",
        lambda: get_object_or_404(
            connections(request.user).select_for_update(), id=connection_id
        ),
        apply,
        lambda x: connection_payload(x, request.user),
    )
