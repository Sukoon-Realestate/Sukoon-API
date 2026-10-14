"""Visit: property visit create apiview."""

import logging
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from core_apps.common.idempotency import (
    execute_idempotent,
    request_key as get_idempotency_key,
    response_headers,
)
from core_apps.common.pagination import StandardResultsSetPagination
from core_apps.common.renderers import GenericJsonRenderer
from ...models import Property
from ...serializers import (
    AvailableDatesQuerySerializer,
    OwnerAvailabilityWeekQuerySerializer,
    OwnerAvailabilityDayUpdateSerializer,
    OwnerVisitCalendarQuerySerializer,
    PropertyVisitCreateSerializer,
    TenantVisitRequestDetailSerializer,
)
from ...serializers.visit import get_visit_language
from ...services import PropertyVisitService


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
        request_key = get_idempotency_key(request)

        def create_visit():
            visit = serializer.save(tenant=request.user, property_obj=property_obj)
            response_data = TenantVisitRequestDetailSerializer(
                visit, context={"request": request}
            ).data
            return (
                {"message": "Visit request submitted successfully.", **response_data},
                status.HTTP_201_CREATED,
                visit.id,
            )

        data, response_status, replayed = execute_idempotent(
            user=request.user,
            operation=f"property.visit.create:{property_obj.id}",
            key=request_key,
            payload=serializer.validated_data,
            action=create_visit,
            request_subject_id=property_obj.id,
        )
        return Response(
            data,
            status=response_status,
            headers=response_headers(replayed),
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
            language=get_visit_language(request),
        )
        return Response(calendar)
