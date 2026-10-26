from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from core_apps.properties.models import Property
from ..planning_models import GroupProcess, HousingGroup
from ..rental_lifecycle_serializers import (
    BookingBody,
    ConsentBody,
    CommandBody,
    GroupTermsDecisionBody,
    GroupTermsRevisionBody,
    GroupBookingFilters,
)
from ..services.rental_lifecycle.access import booking_queryset
from ..services.rental_lifecycle.group_bookings import (
    create_booking,
    booking_payload,
    booking_action,
    current_roster,
)
from .common import endpoint, validated, mutate, page


def application_parties(identity):
    from core_apps.users.models import User

    item = get_object_or_404(
        GroupProcess.objects.select_related("property"), id=identity
    )
    return {
        item.property.owner_id,
        *User.objects.filter(id__in=item.participant_ids).values_list("pk", flat=True),
    }


def booking_parties(identity):
    from ..models import GroupBookingProposal

    item = get_object_or_404(GroupBookingProposal, id=identity)
    return {item.owner_id, *item.participants.values_list("tenant_id", flat=True)}


@endpoint(["GET", "POST"])
def group_bookings(request):
    if request.method == "GET":
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

    return mutate(
        request,
        "group_booking.create",
        authorize,
        execute,
        account_parties=lambda: application_parties(data["application_id"]),
    )


@endpoint(["GET", "POST"])
def group_booking(request, booking_id, action=None):
    item = get_object_or_404(booking_queryset(request.user), id=booking_id)
    if request.method == "GET":
        return Response(
            booking_payload(item, request.user),
            headers={"Cache-Control": "private, no-store"},
        )
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

    def authorize():
        HousingGroup.objects.select_for_update().get(pk=item.group_id)
        Property.objects.select_for_update().get(pk=item.property_id)
        from ..models import GroupBookingProposal

        current = get_object_or_404(booking_queryset(request.user), pk=item.pk)
        return GroupBookingProposal.objects.select_for_update().get(pk=current.pk)

    def execute(current):
        current = booking_action(current, request.user, data, action)
        return current, booking_payload(current, request.user), 200

    return mutate(
        request,
        f"group_booking.{action}.{booking_id}",
        authorize,
        execute,
        account_parties=lambda: booking_parties(booking_id),
    )
