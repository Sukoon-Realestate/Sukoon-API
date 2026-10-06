import logging

from django.db.models import Avg, FloatField, Max, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.response import Response

from core_apps.common.pagination import StandardResultsSetPagination
from core_apps.common.renderers import GenericJsonRenderer

from ..filters import PropertyFilter
from ..models import Property, SavedProperty
from ..serializers import SavedPropertyCardSerializer, SavedPropertySerializer
from ..services import SavedPropertyService

logger = logging.getLogger(__name__)


class SavedPropertyPagination(StandardResultsSetPagination):
    page_size = 9

    def get_paginated_response(self, data):
        """Include the total so the saved-screen heading stays pagination-safe."""
        return Response(
            {
                "count": self.page.paginator.count,
                "per_page": self.page.paginator.per_page,
                "total_pages": self.page.paginator.num_pages,
                "results": data,
            }
        )


class SavedPropertyListAPIView(generics.ListAPIView):
    """
    List the authenticated tenant's saved properties.

    Supports property_type, price_min, price_max, bedrooms, bedrooms_min,
    is_furnished and all amenity filters accepted by the property feed.
    Results can be ordered with ?ordering=saved_at, -saved_at, price or -price.
    """

    serializer_class = SavedPropertyCardSerializer
    renderer_classes = [GenericJsonRenderer]
    pagination_class = SavedPropertyPagination
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PropertyFilter
    search_fields = [
        "title",
        "description",
        "city__name",
        "governorate__name",
        "district",
    ]
    ordering_fields = ["saved_at", "price", "created_at"]
    ordering = ["-saved_at"]

    def get_queryset(self):
        return (
            Property.objects.filter(saves__user=self.request.user)
            .select_related("property_type", "governorate", "city")
            .annotate(
                saved_at=Max("saves__created_at"),
                rating=Coalesce(
                    Avg("ratings__rating"),
                    Value(0.0),
                    output_field=FloatField(),
                ),
            )
            .order_by("-saved_at")
        )


class SavedPropertyCreateAPIView(generics.GenericAPIView):
    """Save one property for the authenticated tenant (request body: {})."""

    serializer_class = SavedPropertySerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        property_obj = get_object_or_404(Property, id=self.kwargs["property_id"])
        saved_property, created = SavedPropertyService.save_property(
            user=request.user,
            property_obj=property_obj,
        )
        serializer = self.get_serializer(saved_property)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        message = "Property saved." if created else "Property was already saved."
        return Response(
            {"message": message, **serializer.data},
            status=response_status,
        )


class SavedPropertyDeleteAPIView(generics.DestroyAPIView):
    """Remove one property from the authenticated tenant's saved list."""

    serializer_class = SavedPropertySerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        saved_property = get_object_or_404(
            SavedProperty.objects.select_related("property"),
            user=self.request.user,
            property__id=self.kwargs["property_id"],
        )
        self.check_object_permissions(self.request, saved_property)
        return saved_property

    def perform_destroy(self, instance):
        SavedPropertyService.remove_saved_property(instance)
