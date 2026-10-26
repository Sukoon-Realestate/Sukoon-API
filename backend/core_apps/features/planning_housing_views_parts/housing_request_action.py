"""Planning housing views: housing request action."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..planning_models import HousingOffer
from ..services.planning import money, mutate, planning_api
from .housing_requests import (
    request_status,
    get_request,
    request_actions,
    request_payload,
    _request_values,
)


@planning_api(["POST"], "housing_requests")
def housing_request_action(request, request_id, action):
    def apply(item, revision):
        if item.user_id != request.user.pk or action not in request_actions(
            request.user, item
        ):
            raise PermissionDenied("This request action is not available to you.")
        if request.data.get("action") != action:
            raise ValidationError({"action": "Body and route action must match."})
        if action == "edit":
            from ..services.housing_request_reviews import edit_content

            edit_content(item, _request_values(request.data, previous=item.criteria), request.user)
        else:
            item.status = {
                "pause": "paused",
                "publish": "published",
                "close": "closed",
                "fulfill": "fulfilled",
            }[action]
        item.revision += 1
        item.save()
        return item

    return mutate(
        request,
        f"housing_request.{action}.{request_id}",
        lambda: get_request(request.user, request_id, lock=True),
        apply,
        lambda x: request_payload(x, request.user),
    )


def offer_status(item, *, existing_process=False):
    from ..services.housing_request_reviews import LIVE, TERMINAL, incompatibility
    from ..services.student_housing.publication import request_current

    if item.status in TERMINAL or item.status == "tender_quote":
        return item.status
    if request_status(item.request) != "published":
        return (
            "request_closed"
            if item.request.status in {"closed", "fulfilled"}
            else "expired"
        )
    if not request_current(item.request):
        return "review_required"
    if item.request.academic_plan_id:
        from ..services.student_housing.policies import response_policy_current
        if not response_policy_current(item):
            return "review_required"
    if item.review_state == "incompatible":
        return "incompatible"
    if item.status in LIVE and incompatibility(
        item, check_academic_availability=not existing_process
    ):
        return "unavailable"
    if (
        item.reviewed_content_revision != item.request.content_revision
        or item.review_state == "pending_reconfirm"
    ):
        return "pending_reconfirm"
    return (
        "sent" if item.status in {"shortlisted", "selected_to_proceed"} else item.status
    )


def offer_actions(user, item):
    from ..services.housing_request_reviews import LIVE
    from .housing_requests import can_offer_request

    if item.status == "tender_quote" or hasattr(item, "tender_line"):
        return []
    state = offer_status(item)
    if user.pk == item.owner_id:
        if item.status not in LIVE or request_status(item.request) not in {
            "published",
            "paused",
        }:
            return []
        actions = ["withdraw"]
        if can_offer_request(user, item.request):
            actions.append("replace")
            if state == "pending_reconfirm":
                actions.append("reconfirm")
        return actions
    if user.pk == item.request.user_id:
        if state in {"sent", "viewed"}:
            return ["review", "decline"]
        if state in {"pending_reconfirm", "incompatible", "unavailable"}:
            return ["decline"]
    return []


def offer_payload(item, user):
    from ..services.student_housing.publication import participant_can_read

    _check_sealed_offer(user, item)
    from ..services.housing_request_reviews import pending_changes
    from core_apps.common.translation import translate_message

    return {
        "id": str(item.id),
        "request_id": str(item.request.id),
        "owner_user_id": str(item.owner.id),
        "status": offer_status(item),
        "note": item.note,
        "revision": item.revision,
        "request_revision": item.request_revision,
        "current_request_revision": item.request.revision,
        "request_content_revision": item.request.content_revision,
        "reviewed_content_revision": item.reviewed_content_revision,
        "review_state": item.review_state,
        "source_changes": item.source_changes,
        "request_changes": pending_changes(item),
        "review_reasons": [translate_message(reason) for reason in item.review_reasons],
        "replaces_offer_id": str(item.replaces.id) if item.replaces_id else None,
        "selection": item.selection,
        "rent": money(item.rent_minor),
        "deposit": (
            money(item.deposit_minor) if item.deposit_minor is not None else None
        ),
        "price_period": item.price_period,
        "allowed_actions": offer_actions(user, item),
        "blocking_reasons": [],
        "academic_context": item.request.academic_snapshot,
        "student_policy": item.student_policy_snapshot,
        "academic_group_id": (
            str(item.request.academic_plan.group.id)
            if item.request.academic_plan_id
            and item.request.academic_plan.group_id
            and participant_can_read(user, item.request)
            else None
        ),
    }


def get_offer(user, identifier, *, lock=False):
    queryset = HousingOffer.objects.select_related(
        "request", "owner", "property", "replaces"
    )
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    item = get_object_or_404(queryset, id=identifier)
    if _check_sealed_offer(user, item):
        return item
    from ..services.student_housing.publication import participant_can_read

    if (
        item.owner_id != user.pk
        and not (item.request.user_id == user.pk and not item.request.academic_plan_id)
        and not participant_can_read(user, item.request)
    ):
        from rest_framework.exceptions import NotFound

        raise NotFound()
    return item


def _check_sealed_offer(user, item):
    """A canonical bid quote must retain its tender-specific visibility."""
    line = getattr(item, "tender_line", None)
    if line is None and item.status != "tender_quote":
        return False
    from ..services.housing_tenders.access import admin
    from rest_framework.exceptions import NotFound

    if line is None or not (
        line.bid.owner_id == user.pk or admin(user, line.bid.tender)
    ):
        raise NotFound()
    return True
