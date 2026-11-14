"""Planning housing views: owner housing offers."""

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer


from ..planning_models import HousingOffer
from ..services.housing_request_reviews import offer_page
from .housing_request_action import offer_payload


class OwnerHousingOffersView(FeatureAPIView):
    name = "Owner Housing Offers"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "owner_housing_offers",
            "owner_housing_offers",
            boundary="planning",
            capability="housing_offers",
            typed=False,
        ),
    }

    def get(self, request):
        return offer_page(
            request,
            HousingOffer.objects.filter(owner=request.user)
            .filter(tender_line__isnull=True)
            .exclude(status="tender_quote")
            .select_related("request", "owner", "property", "replaces")
            .order_by("-created_at", "pkid"),
            lambda x: offer_payload(x, request.user),
        )


# Stable callable import for integrations; URLs use the explicit class.
owner_housing_offers = OwnerHousingOffersView.as_view()
