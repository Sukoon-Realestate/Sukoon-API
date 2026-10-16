from django.db import transaction
from rest_framework.response import Response
from ..rental_lifecycle_serializers import HoldBody, ReasonBody
from ..services.rental_lifecycle import reservations as service
from ..services.rental_lifecycle.access import property_for, hold_for
from ..services.rental_lifecycle.inventory import expire_property_holds
from .common import endpoint, validated, mutate, page


@endpoint(["GET", "POST"])
def reservation_holds(request, external=False):
    if request.method == "GET":
        from django.db.models import Q
        from ..models import ReservationHold

        qs = ReservationHold.objects.filter(
            Q(actor=request.user) | Q(property__owner=request.user), companybookingitem__isnull=True
        ).order_by("-created_at")
        if request.query_params.get("property_id"):
            qs = qs.filter(property__id=request.query_params["property_id"])
        if external:
            qs = qs.filter(
                property__owner=request.user,
                kind__in=["external_booking", "operational"],
            )
        return page(request, qs, lambda item: service.hold_payload(item, request.user))
    data = validated(HoldBody, request.data)

    def execute(prop):
        item = service.create_hold(prop, request.user, data, external=external)
        return item, service.hold_payload(item, request.user), 201

    return mutate(
        request,
        "availability_block.create" if external else "reservation_hold.create",
        lambda: property_for(
            request.user, data["property_id"], owner=external, lock=True
        ),
        execute,
    )


@endpoint(["GET", "POST"])
def reservation_hold(request, hold_id, action=None):
    if request.method == "GET":
        with transaction.atomic():
            item = hold_for(request.user, hold_id, lock=True)
            expire_property_holds(item.property)
            item.refresh_from_db()
            return Response(service.hold_payload(item, request.user))
    data = validated(ReasonBody, request.data)

    def execute(item):
        item = service.change_hold(item, request.user, data, action)
        return item, service.hold_payload(item, request.user), 200

    return mutate(
        request,
        f"reservation_hold.{action}.{hold_id}",
        lambda: hold_for(request.user, hold_id, lock=True),
        execute,
    )
