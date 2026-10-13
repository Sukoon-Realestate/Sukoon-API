"""Planning housing views: housing request action."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..planning_models import HousingOffer
from ..services.planning import money, mutate, planning_api, public_properties
from ..services.rental_phase2 import RentalConflict
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
            for key, value in _request_values(request.data).items():
                setattr(item, key, value)
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


def offer_status(item):
    if item.status not in {"declined", "withdrawn"} and (
        request_status(item.request) != "published"
        or item.request_revision != item.request.revision
    ):
        return "expired"
    if item.status in {"sent", "viewed", "shortlisted", "selected_to_proceed"}:
        from ..services.tenancy_invitations import resolve_offer_snapshot

        try:
            if not public_properties().filter(pk=item.property_id).exists():
                return "unavailable"
            resolve_offer_snapshot(
                item.property,
                item.selection["offer_id"],
                item.selection["offer_revision"],
            )
        except (ValidationError, RentalConflict, KeyError):
            return "unavailable"
    return item.status


def offer_actions(user, item):
    if user.pk == item.owner_id:
        return (
            ["withdraw"]
            if item.status in {"sent", "viewed", "shortlisted", "selected_to_proceed"}
            else []
        )
    if user.pk == item.request.user_id and offer_status(item) in {
        "sent",
        "viewed",
        "shortlisted",
    }:
        return (["shortlist"] if item.status != "shortlisted" else []) + [
            "select_to_proceed",
            "decline",
        ]
    if user.pk == item.request.user_id and offer_status(item) == "selected_to_proceed":
        return ["decline"]
    return []


def offer_payload(item, user):
    return {
        "id": str(item.id),
        "request_id": str(item.request.id),
        "owner_user_id": str(item.owner.id),
        "status": offer_status(item),
        "note": item.note,
        "revision": item.revision,
        "request_revision": item.request_revision,
        "selection": item.selection,
        "rent": money(item.rent_minor),
        "deposit": money(item.deposit_minor),
        "price_period": item.price_period,
        "allowed_actions": offer_actions(user, item),
        "blocking_reasons": [],
    }


def get_offer(user, identifier, *, lock=False):
    queryset = HousingOffer.objects.select_related("request", "owner")
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    item = get_object_or_404(
        queryset.filter(Q(owner=user) | Q(request__user=user)), id=identifier
    )
    return item
