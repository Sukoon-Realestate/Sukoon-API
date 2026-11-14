from functools import partial
from ..services.rental_lifecycle import reservations_commands as commands

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from django.db import transaction
from rest_framework.response import Response
from ..rental_lifecycle_serializers import HoldBody, ReasonBody
from ..services.rental_lifecycle import reservations as service
from ..services.rental_lifecycle.access import property_for, hold_for
from ..services.rental_lifecycle.inventory import expire_property_holds
from .common import validated, mutate, page


class ReservationHoldsView(FeatureAPIView):
    name = "Reservation Holds"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "reservations",
            "reservation_holds",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "reservations",
            "reservation_holds",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, external=False):
        from django.db.models import Q
        from ..models import ReservationHold

        qs = ReservationHold.objects.filter(
            Q(actor=request.user) | Q(property__owner=request.user),
            companybookingitem__isnull=True,
        ).order_by("-created_at")
        if request.query_params.get("property_id"):
            qs = qs.filter(property__id=request.query_params["property_id"])
        if external:
            qs = qs.filter(
                property__owner=request.user,
                kind__in=["external_booking", "operational"],
            )
        return page(request, qs, lambda item: service.hold_payload(item, request.user))

    def post(self, request, external=False):
        data = validated(HoldBody, request.data)
        execute = partial(
            commands.reservation_holds_post_execute,
            actor=request.user,
            data=data,
            external=external,
        )
        return mutate(
            request,
            "availability_block.create" if external else "reservation_hold.create",
            lambda: property_for(
                request.user, data["property_id"], owner=external, lock=True
            ),
            execute,
            account_parties=lambda: {
                request.user.pk,
                property_for(request.user, data["property_id"]).owner_id,
            },
        )


# Stable callable import for integrations; URLs use the explicit class.
reservation_holds = ReservationHoldsView.as_view()


class ReservationHoldView(FeatureAPIView):
    name = "Reservation Hold"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "reservations",
            "reservation_hold",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "reservations",
            "reservation_hold",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, hold_id, action=None):
        with transaction.atomic():
            item = hold_for(request.user, hold_id, lock=True)
            expire_property_holds(item.property)
            item.refresh_from_db()
            return Response(service.hold_payload(item, request.user))

    def post(self, request, hold_id, action=None):
        data = validated(ReasonBody, request.data)
        execute = partial(
            commands.reservation_hold_post_execute,
            action=action,
            actor=request.user,
            data=data,
        )
        return mutate(
            request,
            f"reservation_hold.{action}.{hold_id}",
            lambda: hold_for(request.user, hold_id, lock=True),
            execute,
        )


# Stable callable import for integrations; URLs use the explicit class.
reservation_hold = ReservationHoldView.as_view()
