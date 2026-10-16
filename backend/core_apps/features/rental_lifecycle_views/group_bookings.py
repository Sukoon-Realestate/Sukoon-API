from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from core_apps.properties.models import Property
from ..planning_models import GroupProcess, HousingGroup
from ..rental_lifecycle_serializers import BookingBody, ConsentBody, CommandBody
from ..services.rental_lifecycle.access import booking_queryset
from ..services.rental_lifecycle.group_bookings import (
    create_booking,
    booking_payload,
    booking_action,
)
from .common import endpoint, validated, mutate, page


@endpoint(["GET", "POST"])
def group_bookings(request):
    if request.method == "GET":
        qs = booking_queryset(request.user).order_by("-created_at")
        if request.query_params.get("group_id"):
            qs = qs.filter(group__id=request.query_params["group_id"])
        return page(request, qs, lambda item: booking_payload(item, request.user))
    data = validated(BookingBody, request.data)

    def authorize():
        item = get_object_or_404(
            GroupProcess, id=data["application_id"], property__owner=request.user
        )
        HousingGroup.objects.select_for_update().get(pk=item.group_id)
        Property.objects.select_for_update().get(pk=item.property_id)
        return GroupProcess.objects.select_for_update().get(pk=item.pk)

    def execute(application):
        item = create_booking(application, request.user, data)
        return item, booking_payload(item, request.user), 201

    return mutate(request, "group_booking.create", authorize, execute)


@endpoint(["GET", "POST"])
def group_booking(request, booking_id, action=None):
    item = get_object_or_404(booking_queryset(request.user), id=booking_id)
    if request.method == "GET":
        return Response(booking_payload(item, request.user))
    data = validated(
        ConsentBody if action == "consent_group_booking" else CommandBody, request.data
    )

    def authorize():
        HousingGroup.objects.select_for_update().get(pk=item.group_id)
        Property.objects.select_for_update().get(pk=item.property_id)
        from ..models import GroupBookingProposal

        return GroupBookingProposal.objects.select_for_update().get(pk=item.pk)

    def execute(current):
        current = booking_action(current, request.user, data, action)
        return current, booking_payload(current, request.user), 200

    return mutate(request, f"group_booking.{action}.{booking_id}", authorize, execute)
