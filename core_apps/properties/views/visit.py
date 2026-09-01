import logging
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from core_apps.common.pagination import StandardResultsSetPagination
from core_apps.common.renderers import GenericJsonRenderer

from ..filters import PropertyVisitFilter
from ..models import Property, PropertyVisit
from ..permissions import IsTenantOrPropertyOwner
from ..serializers import (
    AvailableDatesQuerySerializer,
    OwnerAvailabilityWeekQuerySerializer,
    OwnerAvailabilityDayUpdateSerializer,
    OwnerVisitCalendarQuerySerializer,
    PropertyVisitCreateSerializer,
    PropertyVisitDetailSerializer,
    PropertyVisitSerializer,
    PropertyVisitUpdateSerializer,
    TenantVisitListSerializer,
    PropertyVisitReviewSerializer,
    TenantVisitRequestDetailSerializer,
    TenantVisitRequestSerializer,
)
from ..services import PropertyVisitService

logger = logging.getLogger(__name__)


class PropertyVisitPagination(StandardResultsSetPagination):
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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        property_obj = get_object_or_404(
            Property.objects.select_related(
                "owner", "owner__profile", "property_type", "governorate", "city"
            ),
            id=self.kwargs["property_id"],
        )
        visit = serializer.save(tenant=request.user, property_obj=property_obj)
        response_data = TenantVisitRequestDetailSerializer(
            visit, context={"request": request}
        ).data
        return Response(
            {"message": "Visit request submitted successfully.", **response_data},
            status=status.HTTP_201_CREATED,
        )


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


class OwnerAvailabilityWeekAPIView(generics.GenericAPIView):
    """Read or save one of the authenticated owner's property availability grids.

    Request Body Example (PUT):
    {
        "availability_date": "2026-09-15",
        "slots": [
            {"time": "09:00:00", "is_enabled": true},
            {"time": "12:00:00", "is_enabled": true}
        ]
    }

    Empty ``slots`` clears every non-booked slot on the selected date. Booked
    slots are always preserved and cannot be disabled.
    """

    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get_property(self):
        return get_object_or_404(
            Property.objects.select_related("owner"),
            id=self.kwargs["property_id"],
            owner=self.request.user,
        )

    def get(self, request, *args, **kwargs):
        serializer = OwnerAvailabilityWeekQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        start_date = serializer.validated_data.get("start_date")
        if start_date is None:
            today = timezone.localdate()
            start_date = today - timedelta(days=today.weekday())
        return Response(
            PropertyVisitService.get_owner_availability(self.get_property(), start_date)
        )

    def put(self, request, *args, **kwargs):
        serializer = OwnerAvailabilityDayUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        schedule = PropertyVisitService.replace_property_day_availability(
            property_obj=self.get_property(),
            availability_date=serializer.validated_data["availability_date"],
            slots_data=serializer.validated_data["slots"],
        )
        return Response({"message": "Availability saved successfully.", **schedule})


class OwnerVisitCalendarAPIView(generics.GenericAPIView):
    """Return calendar indicators and the owner visits for a selected month day."""

    serializer_class = OwnerVisitCalendarQuerySerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        calendar = PropertyVisitService.get_owner_visit_calendar(
            owner=request.user,
            year=data["year"],
            month=data["month"],
            selected_date=data.get("date"),
        )
        return Response(calendar)


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
        return PropertyVisit.objects.filter(tenant=self.request.user).select_related(
            "property",
            "property__owner",
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
        return PropertyVisit.objects.filter(tenant=self.request.user).select_related(
            "property",
            "property__owner",
            "property__owner__profile",
            "property__property_type",
            "property__governorate",
            "property__city",
            "review",
        )


class PropertyVisitCancelAPIView(generics.GenericAPIView):
    """Cancel one of the authenticated tenant's pending or confirmed visits.

    Request Body Example:
    {}
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
        visit = PropertyVisitService.update_visit_status(
            user=request.user,
            visit_obj=visit,
            status=PropertyVisit.Status.CANCELED,
        )
        data = TenantVisitRequestDetailSerializer(
            visit, context={"request": request}
        ).data
        return Response({"message": "Visit canceled successfully.", **data})


class PropertyVisitReviewCreateAPIView(generics.GenericAPIView):
    """Submit the rating sheet for a completed, confirmed visit.

    Request Body Example:
    {
        "overall_rating": 4,
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
        review = PropertyVisitService.create_review(
            tenant=request.user,
            visit_obj=visit,
            validated_data=serializer.validated_data,
        )
        return Response(
            {
                "message": "Visit review submitted successfully.",
                **self.get_serializer(review).data,
            },
            status=status.HTTP_201_CREATED,
        )
