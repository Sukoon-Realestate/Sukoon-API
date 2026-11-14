"""Named group bookings commands; adapters supply typed data and current actor."""

from django.shortcuts import get_object_or_404
from core_apps.properties.models import Property
from core_apps.features.planning_models import GroupProcess, HousingGroup
from core_apps.features.services.rental_lifecycle.access import booking_queryset
from core_apps.features.services.rental_lifecycle.group_bookings import (
    create_booking,
    booking_payload,
    booking_action,
)


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
    from core_apps.features.models import GroupBookingProposal

    item = get_object_or_404(GroupBookingProposal, id=identity)
    return {item.owner_id, *item.participants.values_list("tenant_id", flat=True)}


def group_bookings_post_authorize(*, actor, data):
    item = get_object_or_404(
        GroupProcess, id=data["application_id"], property__owner=actor
    )
    HousingGroup.objects.select_for_update().get(pk=item.group_id)
    Property.objects.select_for_update().get(pk=item.property_id)
    return GroupProcess.objects.select_for_update().get(pk=item.pk)


def group_bookings_post_execute(application, *, actor, data):
    item = create_booking(application, actor, data)
    return (item, booking_payload(item, actor), 201)


def group_booking_post_authorize(*, actor, item):
    HousingGroup.objects.select_for_update().get(pk=item.group_id)
    Property.objects.select_for_update().get(pk=item.property_id)
    from core_apps.features.models import GroupBookingProposal

    current = get_object_or_404(booking_queryset(actor), pk=item.pk)
    return GroupBookingProposal.objects.select_for_update().get(pk=current.pk)


def group_booking_post_execute(current, *, action, actor, data):
    current = booking_action(current, actor, data, action)
    return (current, booking_payload(current, actor), 200)
