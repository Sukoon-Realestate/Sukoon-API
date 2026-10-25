"""Fresh, request-specific accommodation choices for the responding owner."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from core_apps.properties.serializers import PropertyDetailSerializer
from ..services.planning import planning_api, public_properties, offer_money
from ..services.housing_offer_matching import offer_problem, property_requirements
from ..services.tenancy_invitations import resolve_offer_snapshot, InvitationConflict
from ..services.rental_phase2 import RentalConflict
from ..services.student_housing.policies import validate_response
from .housing_requests import get_request, can_offer_request


@planning_api(["GET"], "housing_offers")
def housing_offer_inventory(request, request_id, property_id):
    parent = get_request(request.user, request_id)
    if not can_offer_request(request.user, parent):
        raise PermissionDenied(
            "Only an eligible owner can respond to a published request."
        )
    prop = get_object_or_404(
        property_requirements(public_properties(), parent.criteria)
        .filter(owner=request.user, is_ownership_verified=True)
        .select_related("property_type", "owner", "city", "governorate")
        .prefetch_related("images"),
        id=property_id,
    )
    data = PropertyDetailSerializer(prop, context={"request": request}).data
    inventory = data["rental_inventory"]
    matches = []
    for offer in inventory.get("offers", []):
        if offer.get("archived") or offer.get("availability") != "available":
            continue
        try:
            _, snapshot = resolve_offer_snapshot(
                prop, offer["id"], offer["revision"], request
            )
            rent, _ = offer_money(snapshot)
            if offer_problem(parent, prop, snapshot, rent):
                continue
            if parent.academic_plan_id:
                validate_response(parent, prop, snapshot)
        except (ValidationError, RentalConflict, InvitationConflict):
            # Unavailable/stale/incomplete inventory is not a selectable offer.
            continue
        matches.append(offer)
    inventory["offers"] = matches
    return Response(data)
