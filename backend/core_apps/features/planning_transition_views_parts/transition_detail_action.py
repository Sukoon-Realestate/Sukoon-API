"""Planning transition views: transition detail action."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from ..planning_models import TenancyTransition
from ..planning_condition_views import participant_lease
from ..services.planning import (
    check_revision,
    civil_date,
    display_name,
    mutate,
    page,
    planning_api,
    require_planning,
    text_field,
)
from ..services.rental_phase2 import RentalConflict
from .transition_projection import (
    TERMINAL,
    transition_actions,
    transition_payload,
    transition_for,
    _candidates,
    _nominate,
)


def _transition_list(request, lease_id, kind):
    require_planning(
        request.user, "move_out_notices" if kind == "moveOutNotice" else "replacements"
    )
    lease = participant_lease(request.user, lease_id)
    if request.method == "GET":
        return page(
            request,
            lease.planning_transitions.filter(kind=kind).order_by(
                "-created_at", "pkid"
            ),
            lambda x: transition_payload(x, request.user),
        )

    def apply(lease, revision):
        from ..services.planning_transitions import require_no_renewal

        require_no_renewal(lease)
        if lease.legacy_read_only or lease.status not in {
            "active",
            "termination_pending",
        }:
            raise RentalConflict(
                "Only a current tenancy can submit a notice or replacement request."
            )
        if (
            request.data.get("kind") != kind
            or request.data.get("action") != "submit"
            or str(request.data.get("lease_id")) != str(lease.id)
        ):
            raise ValidationError("Kind, action and lease must match the route.")
        if (
            lease.planning_transitions.filter(kind=kind)
            .exclude(status__in=TERMINAL)
            .exists()
        ):
            raise RentalConflict(
                "Resolve the existing request before submitting another."
            )
        day = civil_date(request.data.get("requested_on"), "requested_on", future=True)
        if day < lease.start_date:
            raise ValidationError(
                {"requested_on": "The date cannot precede the lease."}
            )
        item = TenancyTransition(
            lease=lease,
            author=request.user,
            kind=kind,
            requested_on=day,
            reason=text_field(request.data, "reason", required=True),
            history=["Request received; the lease and possession remain unchanged."],
        )
        if request.data.get("candidate_id"):
            if kind != "replacement":
                raise ValidationError(
                    {"candidate_id": "Candidates belong to replacement requests."}
                )
            _nominate(request, item)
        item.save()
        return item

    return mutate(
        request,
        f"transition.{kind}.create.{lease_id}",
        lambda: participant_lease(request.user, lease_id, lock=True),
        apply,
        lambda x: transition_payload(x, request.user),
        creating=True,
    )


@planning_api(["GET", "POST"], "move_out_notices")
def move_out_notices(request, lease_id):
    return _transition_list(request, lease_id, "moveOutNotice")


@planning_api(["GET", "POST"], "replacements")
def replacement_requests(request, lease_id):
    return _transition_list(request, lease_id, "replacement")


@planning_api(["GET", "POST"], None)
def transition_detail_action(request, transition_id, kind, action=None):
    # Notice and replacement switches remain independent of housing groups.
    require_planning(
        request.user, "move_out_notices" if kind == "moveOutNotice" else "replacements"
    )
    if request.method == "GET":
        if action:
            raise NotFound()
        return Response(
            transition_payload(
                transition_for(request.user, transition_id, kind), request.user
            )
        )

    def apply(item, revision):
        if action not in transition_actions(request.user, item):
            raise PermissionDenied("This transition action is not available to you.")
        if (
            request.data.get("action") != action
            or request.data.get("kind") != kind
            or str(request.data.get("lease_id")) != str(item.lease.id)
        ):
            raise ValidationError("Kind, action and lease must match the transition.")
        if action == "acknowledge":
            item.status = "acknowledged"
        elif action == "nominate":
            _nominate(request, item)
        elif action == "approve_availability":
            from ..services.planning_transitions import require_no_renewal

            require_no_renewal(item.lease)
            item.availability_approved = True
        elif action == "approve_candidate":
            from ..services.planning_transitions import require_no_renewal

            require_no_renewal(item.lease)
            candidate = get_object_or_404(_candidates(item.lease), pk=item.candidate_id)
            check_revision(candidate.revision, item.candidate_revision)
            if not item.candidate_consented:
                raise RentalConflict(
                    "The current candidate has not consented.", code="consent_required"
                )
            item.candidate_approved = True
            item.status = "signatures_pending"
        else:
            item.status = {
                "withdraw": "withdrawn",
                "decline": "declined",
                "cancel": "cancelled",
            }[action]
        item.history.append(
            f"{action} by {display_name(request.user)} at revision {item.revision + 1}."
        )
        item.revision += 1
        item.save()
        return item

    return mutate(
        request,
        f"transition.{action}.{transition_id}",
        lambda: transition_for(request.user, transition_id, kind, lock=True),
        apply,
        lambda x: transition_payload(x, request.user),
    )
