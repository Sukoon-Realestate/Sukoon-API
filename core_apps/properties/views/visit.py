import logging

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from core_apps.common.renderers import GenericJsonRenderer

from ..filters import PropertyVisitFilter
from ..models import Property, PropertyVisit
from ..permissions import IsTenantOrPropertyOwner
from ..serializers import (
    AvailableDatesQuerySerializer,
    PropertyVisitCreateSerializer,
    PropertyVisitDetailSerializer,
    PropertyVisitSerializer,
    PropertyVisitUpdateSerializer,
    TenantVisitListSerializer,
)
from ..services import PropertyVisitService

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

    def perform_create(self, serializer):
        property_obj = get_object_or_404(
            Property.objects.all(), id=self.kwargs["property_id"]
        )
        serializer.save(tenant=self.request.user, property_obj=property_obj)


class PropertyAvailableDatesAPIView(generics.GenericAPIView):
    """Return the property's owner's future visit availability.

    Dates and past-slot checks use the configured Africa/Cairo timezone.
    """

    serializer_class = AvailableDatesQuerySerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        property_obj = get_object_or_404(
            Property.objects.select_related("owner"), id=self.kwargs["property_id"]
        )
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        schedule = PropertyVisitService.get_available_dates(
            property_obj=property_obj,
            requested_date=serializer.validated_data.get("date"),
        )
        return Response(schedule)


class TenantPropertyVisitListAPIView(generics.ListAPIView):
    """
    API view to list all visits requested by the authenticated tenant.

    Returns a compact card-style payload per visit: title (property + district),
    Arabic-formatted visit day/time and an Arabic status label.

    Filters:
    - status (e.g. ?status=confirmed) — one of: pending, confirmed, canceled, rejected
    """

    serializer_class = TenantVisitListSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PropertyVisitPagination
    filterset_class = PropertyVisitFilter

    def get_queryset(self):
        return (
            PropertyVisit.objects.filter(tenant=self.request.user)
            .select_related("property", "property__owner", "tenant")
            .all()
        )


class OwnerPropertyVisitListAPIView(generics.ListAPIView):
    """
    API view to list all visit requests received for properties owned by the authenticated user.

    Returns a trimmed payload per visit: tenant (name, avatar, is_verified),
    visit date, and visit status.

    Filters:
    - status (e.g. ?status=pending) — one of: pending, confirmed, canceled, rejected
    """

    serializer_class = PropertyVisitDetailSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PropertyVisitPagination
    filterset_class = PropertyVisitFilter

    def get_queryset(self):
        return (
            PropertyVisit.objects.filter(property__owner=self.request.user)
            .select_related("tenant", "tenant__profile")
            .all()
        )


class PropertyVisitDetailAPIView(generics.RetrieveAPIView):
    """
    API view to retrieve details of a specific property visit request.

    Returns a trimmed payload: tenant (name, avatar, is_verified),
    visit date, and visit status.
    """

    queryset = PropertyVisit.objects.select_related(
        "property", "property__owner", "tenant", "tenant__profile"
    ).all()
    serializer_class = PropertyVisitDetailSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated, IsTenantOrPropertyOwner]
    lookup_field = "id"

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

    queryset = PropertyVisit.objects.select_related(
        "property", "property__owner", "tenant"
    ).all()
    serializer_class = PropertyVisitUpdateSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated, IsTenantOrPropertyOwner]
    lookup_field = "id"

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), id=self.kwargs["id"])
        self.check_object_permissions(self.request, obj)
        return obj
