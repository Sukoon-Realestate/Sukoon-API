"""Visit: property visit review create apiview."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from core_apps.common.idempotency import (
    execute_idempotent,
    request_key as get_idempotency_key,
    response_headers,
)
from core_apps.common.pagination import StandardResultsSetPagination
from core_apps.common.renderers import GenericJsonRenderer
from ...models import PropertyVisit
from ...serializers import PropertyVisitReviewSerializer
from ...services import PropertyVisitService
from ..viewing_commands import execute_visit_response


class PropertyVisitCancelAPIView(generics.GenericAPIView):
    """Cancel one of the authenticated tenant's pending or confirmed visits.

    Request Body Example:
    {"expected_revision": 1, "request_key": "original-request-uuid"}
    """

    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        visit = get_object_or_404(
            PropertyVisit.objects.select_related(
                "tenant",
                "property",
                "property__owner",
                "property__owner__profile",
                "property__property_type",
                "property__governorate",
                "property__city",
                "review",
            ),
            id=self.kwargs["id"],
            tenant=request.user,
        )
        return execute_visit_response(request, visit.id, "cancel")


class PropertyVisitReviewCreateAPIView(generics.GenericAPIView):
    """Submit the rating sheet for a completed, confirmed visit.

    Request Body Example:
    {
        "cleanliness_rating": 4,
        "listing_accuracy_rating": 5,
        "owner_interaction_rating": 4,
        "comment": "The apartment matched the listing."
    }
    """

    serializer_class = PropertyVisitReviewSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        visit = get_object_or_404(
            PropertyVisit.objects.select_related("tenant", "property"),
            id=self.kwargs["id"],
            tenant=request.user,
        )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_key = get_idempotency_key(request)

        def create_review():
            review = PropertyVisitService.create_review(
                tenant=request.user,
                visit_obj=visit,
                validated_data=serializer.validated_data,
            )
            return (
                {
                    "message": "Visit review submitted successfully.",
                    **self.get_serializer(review).data,
                },
                status.HTTP_201_CREATED,
                review.id,
            )

        data, response_status, replayed = execute_idempotent(
            user=request.user,
            operation=f"property.visit.review:{visit.id}",
            key=request_key,
            payload=serializer.validated_data,
            action=create_review,
            request_subject_id=visit.id,
        )
        return Response(
            data,
            status=response_status,
            headers=response_headers(replayed),
        )


class PropertyReviewPagination(StandardResultsSetPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        summary = getattr(self, "summary", None)
        if summary is not None:
            response.data["summary"] = summary
        return response
