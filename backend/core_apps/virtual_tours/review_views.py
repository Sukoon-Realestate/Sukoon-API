"""Private revision list/detail shared by both administrative deployments."""

from rest_framework.response import Response
from .http import ReviewerTourAPIView
from .review_reads import review_collection, review_detail


class CollectionAPIView(ReviewerTourAPIView):
    http_method_names = ["get", "options"]
    name = "Collection"

    def get(self, request):
        return Response(
            review_collection(
                request.user,
                request.query_params.get("state", "pending"),
                request.query_params.get("page", "1"),
            )
        )


class DetailAPIView(ReviewerTourAPIView):
    http_method_names = ["get", "options"]
    name = "Detail"

    def get(self, request, revision_id):
        return Response(review_detail(request.user, revision_id))
