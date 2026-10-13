"""Visit: property review list apiview."""

from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from core_apps.common.renderers import GenericJsonRenderer
from ...filters import PropertyVisitFilter
from ...models import Property, PropertyVisit, PropertyVisitReview
from ...serializers import (
    OwnerVisitRequestCardSerializer,
    OwnerVisitRequestDetailSerializer,
    PropertyReviewItemSerializer,
)
from .property_visit_create_apiview import PropertyVisitPagination
from .property_visit_review_create_apiview import PropertyReviewPagination


class PropertyReviewListAPIView(generics.ListAPIView):
    """
    API view to list all reviews and ratings for a specific property.
    Accessible publicly without authentication.
    """

    serializer_class = PropertyReviewItemSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.AllowAny]
    pagination_class = PropertyReviewPagination

    def get_property(self):
        if not hasattr(self, "_property_obj"):
            self._property_obj = get_object_or_404(
                Property.objects.only("id", "pkid"), id=self.kwargs["property_id"]
            )
        return self._property_obj

    def get_queryset(self):
        property_obj = self.get_property()
        return (
            PropertyVisitReview.objects.filter(visit__property=property_obj)
            .select_related("visit__tenant", "visit__tenant__profile")
            .order_by("-created_at")
        )

    def list(self, request, *args, **kwargs):
        property_obj = self.get_property()
        aggregates = PropertyVisitReview.objects.filter(
            visit__property=property_obj
        ).aggregate(
            total_reviews=models.Count("id"),
            avg_overall=models.Avg("overall_rating"),
            avg_cleanliness=models.Avg("cleanliness_rating"),
            avg_accuracy=models.Avg("listing_accuracy_rating"),
            avg_interaction=models.Avg("owner_interaction_rating"),
        )
        self._review_summary = {
            "total_reviews": aggregates["total_reviews"],
            "average_rating": (
                round(float(aggregates["avg_overall"]), 1)
                if aggregates["avg_overall"] is not None
                else 0.0
            ),
            "cleanliness_rating": (
                round(float(aggregates["avg_cleanliness"]), 1)
                if aggregates["avg_cleanliness"] is not None
                else 0.0
            ),
            "listing_accuracy_rating": (
                round(float(aggregates["avg_accuracy"]), 1)
                if aggregates["avg_accuracy"] is not None
                else 0.0
            ),
            "owner_interaction_rating": (
                round(float(aggregates["avg_interaction"]), 1)
                if aggregates["avg_interaction"] is not None
                else 0.0
            ),
        }
        return super().list(request, *args, **kwargs)

    def paginate_queryset(self, queryset):
        page = super().paginate_queryset(queryset)
        if page is not None and hasattr(self, "_review_summary"):
            self.paginator.summary = self._review_summary
        return page


class OwnerVisitRequestPagination(PropertyVisitPagination):
    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        request = getattr(self, "request", None)
        if request and request.user.is_authenticated:
            counts = PropertyVisit.objects.filter(
                property__owner=request.user
            ).aggregate(
                new=models.Count(
                    "id", filter=models.Q(status=PropertyVisit.Status.PENDING)
                ),
                pending=models.Count(
                    "id", filter=models.Q(status=PropertyVisit.Status.PENDING)
                ),
                confirmed=models.Count(
                    "id", filter=models.Q(status=PropertyVisit.Status.CONFIRMED)
                ),
                rejected=models.Count(
                    "id", filter=models.Q(status=PropertyVisit.Status.REJECTED)
                ),
                all=models.Count("id"),
            )
            response.data["tabs"] = counts
        return response


class OwnerVisitRequestListAPIView(generics.ListAPIView):
    """
    API view to list all visit requests received for the authenticated owner's properties.
    Designed for the Owner Visit Requests screen (Screen 1).

    Filters:
    - status (e.g. ?status=pending, ?status=confirmed, ?status=rejected)
    """

    serializer_class = OwnerVisitRequestCardSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OwnerVisitRequestPagination
    filterset_class = PropertyVisitFilter

    def get_queryset(self):
        return (
            PropertyVisit.objects.filter(property__owner=self.request.user)
            .select_related("tenant", "tenant__profile", "property")
            .order_by("-created_at")
        )


class OwnerVisitRequestDetailAPIView(generics.RetrieveAPIView):
    """
    API view to retrieve single visit request details for the authenticated owner.
    Designed for the Owner Visit Request Details screen (Screen 2).
    """

    serializer_class = OwnerVisitRequestDetailSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return PropertyVisit.objects.filter(
            property__owner=self.request.user
        ).select_related("tenant", "tenant__profile", "property")
