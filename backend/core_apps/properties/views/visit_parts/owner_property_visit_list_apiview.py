"""Visit: owner property visit list apiview."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from core_apps.common.renderers import GenericJsonRenderer
from ...filters import PropertyVisitFilter
from ...models import PropertyVisit
from ...permissions import IsTenantOrPropertyOwner
from ...services.viewing_access import for_user
from ...serializers import (
    PropertyVisitDetailSerializer,
    PropertyVisitUpdateSerializer,
    TenantVisitListSerializer,
    TenantVisitRequestDetailSerializer,
    TenantVisitRequestSerializer,
)
from .property_visit_create_apiview import PropertyVisitPagination
from .property_review_list_apiview import OwnerVisitRequestPagination


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
            for_user(self.request.user)
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
    pagination_class = OwnerVisitRequestPagination
    filterset_class = PropertyVisitFilter

    def get_queryset(self):
        return (
            PropertyVisit.objects.filter(property__owner=self.request.user)
            .select_related("tenant", "tenant__profile", "property", "property__owner")
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


class TenantVisitRequestListAPIView(generics.ListAPIView):
    """List the authenticated tenant's visit-request screen cards.

    Filters:
    - status (e.g. ``?status=confirmed``)
    """

    serializer_class = TenantVisitRequestSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PropertyVisitPagination
    filterset_class = PropertyVisitFilter

    def get_queryset(self):
        return for_user(self.request.user).select_related(
            "property",
            "property__owner",
            "property__owner__profile",
            "property__property_type",
            "property__governorate",
            "property__city",
            "review",
        )


class TenantVisitRequestDetailAPIView(generics.RetrieveAPIView):
    """Return all data needed by the tenant visit-details screen."""

    serializer_class = TenantVisitRequestDetailSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return for_user(self.request.user).select_related(
            "property",
            "property__owner",
            "property__owner__profile",
            "property__property_type",
            "property__governorate",
            "property__city",
            "review",
        )
