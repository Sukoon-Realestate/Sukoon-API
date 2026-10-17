"""Planning housing views: owner housing offers."""

from ..planning_models import HousingOffer
from ..services.planning import page, planning_api
from .housing_request_action import offer_payload


@planning_api(["GET"], "housing_offers")
def owner_housing_offers(request):
    return page(
        request,
        HousingOffer.objects.filter(owner=request.user)
        .filter(tender_line__isnull=True)
        .exclude(status="tender_quote")
        .select_related("request", "owner", "property")
        .order_by("-created_at", "pkid"),
        lambda x: offer_payload(x, request.user),
    )
