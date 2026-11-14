from functools import partial
from ..services.rental_lifecycle import group_bookings_commands as commands

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from ..rental_lifecycle_serializers import (
    BookingBody,
    ConsentBody,
    CommandBody,
    GroupTermsDecisionBody,
    GroupTermsRevisionBody,
    GroupBookingFilters,
)
from ..services.rental_lifecycle.access import booking_queryset
from ..services.rental_lifecycle.group_bookings import booking_payload, current_roster
from .common import validated, mutate, page


class GroupBookingsView(FeatureAPIView):
    name = "Group Bookings"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "group_bookings",
            "group_bookings",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "group_bookings",
            "group_bookings",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        qs = booking_queryset(request.user).order_by("-created_at")
        values = validated(GroupBookingFilters, request.query_params)
        for key, lookup in (
            ("group_id", "group__id"),
            ("property_id", "property__id"),
            ("academic_plan_id", "application__academic_plan__id"),
        ):
            if values.get(key):
                qs = qs.filter(**{lookup: values[key]})
        if values["active_agreements"]:
            qs = qs.filter(
                status="awaiting_participants",
                deadline__gt=timezone.now(),
                participants__tenant=request.user,
                participants__offer_id=values["offer_id"],
                participants__consent_status="pending",
                participants__invitation__isnull=True,
            )
            qs = qs.filter(
                pk__in=[
                    item.pk
                    for item in qs
                    if current_roster(item)
                    and "consent_group_booking"
                    in booking_payload(item, request.user)["allowed_actions"]
                ]
            )
        elif values.get("offer_id"):
            qs = qs.filter(participants__offer_id=values["offer_id"])
        response = page(request, qs, lambda item: booking_payload(item, request.user))
        response["Cache-Control"] = "private, no-store"
        return response

    def post(self, request):
        data = validated(BookingBody, request.data)
        authorize = partial(
            commands.group_bookings_post_authorize, actor=request.user, data=data
        )
        execute = partial(
            commands.group_bookings_post_execute, actor=request.user, data=data
        )
        return mutate(
            request,
            "group_booking.create",
            authorize,
            execute,
            account_parties=lambda: application_parties(data["application_id"]),
        )


# Stable callable import for integrations; URLs use the explicit class.
group_bookings = GroupBookingsView.as_view()


class GroupBookingView(FeatureAPIView):
    name = "Group Booking"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "group_bookings",
            "group_booking",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "group_bookings",
            "group_booking",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, booking_id, action=None):
        item = get_object_or_404(booking_queryset(request.user), id=booking_id)
        return Response(
            booking_payload(item, request.user),
            headers={"Cache-Control": "private, no-store"},
        )

    def post(self, request, booking_id, action=None):
        item = get_object_or_404(booking_queryset(request.user), id=booking_id)
        body_type = {
            "consent_group_booking": ConsentBody,
            "edit_group_terms": GroupTermsRevisionBody,
            "counter_group_terms": GroupTermsRevisionBody,
            "accept_group_terms": GroupTermsDecisionBody,
            "reject_group_terms": GroupTermsDecisionBody,
            "request_group_terms_changes": GroupTermsDecisionBody,
            "withdraw_group_terms": GroupTermsDecisionBody,
        }.get(action, CommandBody)
        data = validated(body_type, request.data)
        authorize = partial(
            commands.group_booking_post_authorize, actor=request.user, item=item
        )
        execute = partial(
            commands.group_booking_post_execute,
            action=action,
            actor=request.user,
            data=data,
        )
        return mutate(
            request,
            f"group_booking.{action}.{booking_id}",
            authorize,
            execute,
            account_parties=lambda: booking_parties(booking_id),
        )


# Stable callable import for integrations; URLs use the explicit class.
group_booking = GroupBookingView.as_view()

# Supported helper import identities.
from ..services.rental_lifecycle.group_bookings_commands import (
    application_parties as application_parties,
    booking_parties as booking_parties,
)
