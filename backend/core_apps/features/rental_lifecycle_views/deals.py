from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from rest_framework.response import Response
from ..models import RentalInterest
from ..rental_serializers import RentalInterestSerializer
from ..services.rental_lifecycle.deals import deal_projection
from .common import page


class RentalDealView(FeatureAPIView):
    name = "Rental Deal"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "deals", "rental_deal", boundary="standard", capability=None, typed=False
        ),
    }

    def get(self, request, subject_id):
        response = Response(deal_projection(request.user, subject_id))
        response["Cache-Control"] = "private, no-store"
        return response


# Stable callable import for integrations; URLs use the explicit class.
rental_deal = RentalDealView.as_view()


class OwnerApplicationQueueView(FeatureAPIView):
    name = "Owner Application Queue"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "deals",
            "owner_application_queue",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        queryset = (
            RentalInterest.objects.filter(property__owner=request.user)
            .exclude(status__in=["withdrawn", "rejected"])
            .select_related("property__owner", "tenant")
            .order_by("response_due_at", "created_at")
        )
        return page(
            request,
            queryset,
            lambda item: RentalInterestSerializer(
                item, context={"request": request}
            ).data,
        )


# Stable callable import for integrations; URLs use the explicit class.
owner_application_queue = OwnerApplicationQueueView.as_view()
