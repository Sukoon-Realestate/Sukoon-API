"""Planning housing views: housing offers."""

from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..planning_models import HousingOffer, HousingRequest
from ..services.planning import (
    check_revision,
    mutate,
    offer_money,
    page,
    planning_api,
    selection,
    text_field,
)
from ..services.rental_phase2 import RentalConflict
from .housing_requests import get_request, request_actions
from .housing_request_action import offer_actions, offer_payload, get_offer


@planning_api(["GET", "POST"], "housing_offers")
def housing_offers(request, request_id):
    parent = get_request(request.user, request_id)
    if request.method == "GET":
        items = (
            parent.offers.all()
            if parent.user_id == request.user.pk
            else parent.offers.filter(owner=request.user)
        )
        return page(
            request,
            items.select_related("request", "owner").order_by("-created_at", "pkid"),
            lambda x: offer_payload(x, request.user),
        )

    def apply(item, revision):
        if item.user_id == request.user.pk or "offer" not in request_actions(
            request.user, item
        ):
            raise PermissionDenied(
                "Only an eligible owner can respond to a published request."
            )
        if str(request.data.get("request_id")) != str(item.id):
            raise ValidationError({"request_id": "Must match the route."})
        check_revision(item.revision, request.data.get("request_revision"))
        prop, snapshot = selection(request, request.data.get("selection"), owned=True)
        if (
            item.offers.filter(
                owner=request.user,
                property=prop,
                request_revision=item.revision,
                selection__offer_id=snapshot["offer_id"],
            )
            .exclude(status__in=["withdrawn", "declined"])
            .exists()
        ):
            raise RentalConflict(
                "An offer for this exact accommodation already exists.",
                code="duplicate_offer",
            )
        if (
            item.offers.filter(
                owner=request.user, created_at__gte=timezone.now() - timedelta(days=1)
            ).count()
            >= settings.PLANNING_OWNER_OFFERS_PER_REQUEST_PER_DAY
        ):
            raise RentalConflict(
                "The offer limit for this request was reached.", code="offer_limit"
            )
        if str(prop.city.id) != item.criteria["city_id"] or (
            item.criteria["rental_scope"]
            and item.criteria["rental_scope"] != snapshot["rental_scope"]
        ):
            raise ValidationError(
                {
                    "selection": "The offer must match the requested city and accommodation scope."
                }
            )
        capacity = 1 if snapshot["rental_scope"] == "bed" else snapshot.get("capacity")
        if capacity is None or item.criteria["people"] > capacity:
            raise ValidationError(
                {"selection": "The accommodation cannot hold the requested party."}
            )
        rent, deposit = offer_money(snapshot)
        requirements = item.criteria
        if rent < (requirements.get("budget_min") or {}).get(
            "amount_minor", 0
        ) or rent > (requirements.get("budget_max") or {}).get(
            "amount_minor", 10**12
        ):
            raise ValidationError(
                {"selection": "The rent is outside the requested budget."}
            )
        if (
            requirements.get("property_type")
            and prop.property_type.slug != requirements["property_type"]
        ):
            raise ValidationError(
                {"selection": "The property type does not match the request."}
            )
        if (
            requirements.get("furnished") is not None
            and prop.is_furnished != requirements["furnished"]
        ):
            raise ValidationError(
                {"selection": "The furnishing requirement is not met."}
            )
        if any(
            not getattr(prop, name if name == "near_metro" else f"has_{name}", False)
            for name in requirements.get("amenities", [])
        ):
            raise ValidationError(
                {"selection": "The requested amenities are not available."}
            )
        if snapshot["terms"].get("price_period") != item.criteria["price_period"]:
            raise ValidationError(
                {"selection": "The offer must use the requested price period."}
            )
        return HousingOffer.objects.create(
            request=item,
            owner=request.user,
            property=prop,
            request_revision=item.revision,
            selection=snapshot,
            note=text_field(request.data, "note"),
            rent_minor=rent,
            deposit_minor=deposit,
            price_period=snapshot["terms"]["price_period"],
        )

    return mutate(
        request,
        f"housing_offer.create.{request_id}",
        lambda: get_request(request.user, request_id, lock=True),
        apply,
        lambda x: offer_payload(x, request.user),
        creating=True,
    )


@planning_api(["POST"], "housing_offers")
def housing_offer_action(request, offer_id, action):
    def apply(item, revision):
        if action not in offer_actions(request.user, item):
            raise PermissionDenied("This offer action is not available to you.")
        if request.data.get("decision") != action:
            raise ValidationError({"decision": "Body and route decision must match."})
        if action in {"shortlist", "select_to_proceed"}:
            selection(request, item.selection)
        if (
            action == "select_to_proceed"
            and item.request.offers.filter(status="selected_to_proceed")
            .exclude(pk=item.pk)
            .exists()
        ):
            raise RentalConflict(
                "Review the previously selected offer before selecting another."
            )
        item.status = {
            "shortlist": "shortlisted",
            "decline": "declined",
            "withdraw": "withdrawn",
            "select_to_proceed": "selected_to_proceed",
        }[action]
        item.revision += 1
        item.save()
        return item

    def load():
        found = get_offer(request.user, offer_id)
        HousingRequest.objects.select_for_update().get(pk=found.request_id)
        return get_offer(request.user, offer_id, lock=True)

    return mutate(
        request,
        f"housing_offer.{action}.{offer_id}",
        load,
        apply,
        lambda x: offer_payload(x, request.user),
    )
