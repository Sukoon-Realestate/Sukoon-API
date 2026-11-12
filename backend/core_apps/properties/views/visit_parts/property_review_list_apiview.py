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
                self._readable_properties().only("id", "pkid"),
                id=self.kwargs["property_id"],
            )
        return self._property_obj

    def _readable_properties(self):
        # A2-01: anonymous/unrelated readers follow the catalog publication policy.
        # The owner, staff and visit participants keep their historical read.
        from django.db.models import Q
        from core_apps.properties.services.public_access import public_properties

        public = public_properties()
        user = self.request.user
        if not getattr(user, "is_authenticated", False):
            return public
        if user.is_staff:
            return Property.objects.all()
        return Property.objects.filter(
            Q(pk__in=public.values("pk")) | Q(owner=user) | Q(visits__tenant=user)
        ).distinct()

    def get_queryset(self):
        property_obj = self.get_property()
        return (
            PropertyVisitReview.objects.filter(visit__property=property_obj)
            .select_related("visit__tenant", "visit__tenant__profile")
            .order_by("-created_at")
        )

    def list(self, request, *args, **kwargs):
        from ...services.public_review_reads import public_visit_page_source, review_card

        rows, summary = public_visit_page_source(self.get_property())
        page = self.paginate_queryset(rows)
        response = self.get_paginated_response([review_card(row) for row in page])
        response.data["summary"] = summary
        response["Cache-Control"] = "private, no-store"
        return response

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
            counts = PropertyVisit.objects.filter(property__owner=request.user).aggregate(
                new=models.Count("id", filter=models.Q(status=PropertyVisit.Status.PENDING)),
                pending=models.Count("id", filter=models.Q(status=PropertyVisit.Status.PENDING)),
                confirmed=models.Count("id", filter=models.Q(status=PropertyVisit.Status.CONFIRMED)),
                rejected=models.Count("id", filter=models.Q(status=PropertyVisit.Status.REJECTED)),
                canceled=models.Count("id", filter=models.Q(status=PropertyVisit.Status.CANCELED)),
                all=models.Count("id"),
            )
            counts["completed"] = 0
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
        return PropertyVisit.objects.filter(property__owner=self.request.user).select_related(
            "tenant", "tenant__profile", "property"
        )
