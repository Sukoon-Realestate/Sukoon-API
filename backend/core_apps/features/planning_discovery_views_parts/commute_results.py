"""Planning discovery views: commute results."""

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer


from django.shortcuts import get_object_or_404
from ..planning_models import CommuteSearch
from ..services.planning import mutate, page
from ..services.rental_phase2 import RentalConflict
from .catalog_matches import catalog_matches, commute_payload
from .commute_searches import _commute


class CommuteCancelView(FeatureAPIView):
    name = "Commute Cancel"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "commute_results",
            "commute_cancel",
            boundary="planning",
            capability="commute",
            typed=False,
        ),
    }

    def post(self, request, search_id):
        def apply(item, revision):
            if item.status not in {"queued", "running"}:
                raise RentalConflict("This search is already complete.")
            item.status = "cancelled"
            item.matches, item.query = [], {}
            item.revision += 1
            item.save()
            return item

        return mutate(
            request,
            f"commute.cancel.{search_id}",
            lambda: get_object_or_404(
                CommuteSearch.objects.select_for_update(),
                id=search_id,
                user=request.user,
            ),
            apply,
            commute_payload,
        )


# Stable callable import for integrations; URLs use the explicit class.
commute_cancel = CommuteCancelView.as_view()


class CommuteResultsView(FeatureAPIView):
    name = "Commute Results"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "commute_results",
            "commute_results",
            boundary="planning",
            capability="commute",
            typed=False,
        ),
    }

    def get(self, request, search_id):
        item = _commute(request.user, search_id)
        if item.status != "succeeded":
            raise RentalConflict(
                "The route search is not complete.",
                code=item.failure_code or "search_pending",
            )
        # Recheck visibility at read time, including after moderation/withdrawal.
        current = {
            str(prop.id): {x["offer_id"] for x in offers}
            for prop, offers in catalog_matches(item.query.get("filters", {}))
        }
        matches = [
            {
                **x,
                "offer_ids": [
                    offer
                    for offer in x["offer_ids"]
                    if offer in current.get(x["property_id"], set())
                ],
            }
            for x in item.matches
        ]
        return page(request, [x for x in matches if x["offer_ids"]], lambda x: x)


# Stable callable import for integrations; URLs use the explicit class.
commute_results = CommuteResultsView.as_view()
