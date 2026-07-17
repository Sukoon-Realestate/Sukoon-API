import logging

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination

from core_apps.common.renderers import GenericJsonRenderer

from ..models import Property, PropertyVisit
from ..permissions import IsTenantOrPropertyOwner
from ..serializers import (
    PropertyVisitCreateSerializer,
    PropertyVisitSerializer,
    PropertyVisitUpdateSerializer,
)

logger = logging.getLogger(__name__)


class PropertyVisitPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class PropertyVisitCreateAPIView(generics.CreateAPIView):
    """
    API view for a tenant to request/book a visit for a property.

    Request Body Example:
    {
        "visit_date": "2026-07-20",
        "visit_time": "14:00:00",
        "note": "Looking forward to seeing the apartment."
    }
    """

    serializer_class = PropertyVisitCreateSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]
    object_label = "visit"

    def perform_create(self, serializer):
        property_obj = get_object_or_404(
            Property.objects.all(), id=self.kwargs["property_id"]
        )
        serializer.save(tenant=self.request.user, property_obj=property_obj)


class TenantPropertyVisitListAPIView(generics.ListAPIView):
    """
    API view to list all visits requested by the authenticated tenant.
    """

    serializer_class = PropertyVisitSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PropertyVisitPagination
    object_label = "visits"

    def get_queryset(self):
        return (
            PropertyVisit.objects.filter(tenant=self.request.user)
            .select_related("property", "property__owner", "tenant")
            .all()
        )


class OwnerPropertyVisitListAPIView(generics.ListAPIView):
    """
    API view to list all visit requests received for properties owned by the authenticated user.
    """

    serializer_class = PropertyVisitSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PropertyVisitPagination
    object_label = "visits"

    def get_queryset(self):
        return (
            PropertyVisit.objects.filter(property__owner=self.request.user)
            .select_related("property", "property__owner", "tenant")
            .all()
        )


class PropertyVisitDetailAPIView(generics.RetrieveAPIView):
    """
    API view to retrieve details of a specific property visit request.
    """

    queryset = (
        PropertyVisit.objects.select_related("property", "property__owner", "tenant")
        .all()
    )
    serializer_class = PropertyVisitSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated, IsTenantOrPropertyOwner]
    lookup_field = "id"
    object_label = "visit"

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), id=self.kwargs["id"])
        self.check_object_permissions(self.request, obj)
        return obj


class PropertyVisitUpdateAPIView(generics.UpdateAPIView):
    """
    API view to update status of a property visit (e.g. confirm, reject, cancel).

    Request Body Example (PATCH):
    {
        "status": "confirmed"
    }
    """

    queryset = (
        PropertyVisit.objects.select_related("property", "property__owner", "tenant")
        .all()
    )
    serializer_class = PropertyVisitUpdateSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated, IsTenantOrPropertyOwner]
    lookup_field = "id"
    object_label = "visit"

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), id=self.kwargs["id"])
        self.check_object_permissions(self.request, obj)
        return obj
