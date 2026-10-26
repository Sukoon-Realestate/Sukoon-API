"""Fresh party checks for company negotiation and operation receipt recovery."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, PermissionDenied
from ...models import (
    CompanyTermsNegotiation,
    CompanyBookingItem,
    Company,
    CompanyMembership,
)


def role(item, user):
    booking = item.booking
    if not user.is_active:
        return ""
    if user.pk == item.owner_id == booking.offer.owner_id:
        return "owner"
    member = CompanyMembership.objects.filter(
        company=booking.request.company, user=user, is_active=True
    ).first()
    if not member:
        return ""
    if (
        user.pk == item.coordinator_id == booking.request.coordinator_id
        and member.is_coordinator
    ):
        return "coordinator"
    if member.pk == booking.assigned_approver_id and member.is_approver:
        return "approver"
    return ""


def get(user, identity, *, lock=False):
    item = get_object_or_404(CompanyTermsNegotiation, id=identity)
    if lock:
        Company.objects.select_for_update().get(pk=item.booking.request.company_id)
        CompanyBookingItem.objects.select_for_update().get(pk=item.booking_id)
        item = CompanyTermsNegotiation.objects.select_for_update().get(pk=item.pk)
    if not role(item, user):
        raise NotFound()
    return item


def start_booking(user, identity):
    from .access import request_for

    initial = get_object_or_404(CompanyBookingItem, id=identity)
    request_for(user, initial.request.id, lock=True)
    item = CompanyBookingItem.objects.select_for_update().get(pk=initial.pk)
    if item.request.coordinator_id != user.pk or item.offer.owner_id == user.pk:
        raise PermissionDenied(
            "The assigned coordinator must negotiate with a distinct owner."
        )
    return item


def parties(identity):
    item = get_object_or_404(CompanyTermsNegotiation, id=identity)
    from .access import booking_account_parties

    return booking_account_parties(item.booking.id) | {
        item.owner_id,
        item.coordinator_id,
    }
