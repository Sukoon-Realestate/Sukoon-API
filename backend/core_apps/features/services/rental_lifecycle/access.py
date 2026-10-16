"""Fresh relationship checks, including operation-recovery result subjects."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from core_apps.properties.models import Property
from ...models import (
    ApplicationProfile,
    ApplicationProfileVersion,
    ApplicationAccessGrant,
    ReservationHold,
    GroupBookingProposal,
    PropertyDecisionFact,
    RentalAvailabilityConfirmation,
)
from .cases import case_queryset


def property_for(user, identifier, *, owner=False, lock=False):
    qs = Property.objects.select_related("owner")
    if lock:
        qs = qs.select_for_update(of=("self",))
    condition = (
        Q(owner=user)
        if owner
        else Q(owner=user) | Q(status="verified", is_verified=True)
    )
    return get_object_or_404(qs.filter(condition), id=identifier)


def hold_for(user, identifier, *, lock=False):
    scoped = ReservationHold.objects.filter(
        Q(actor=user) | Q(property__owner=user), companybookingitem__isnull=True
    )
    item = get_object_or_404(scoped, id=identifier)
    if lock:
        Property.objects.select_for_update().get(pk=item.property_id)
        item = scoped.select_for_update(of=("self",)).get(pk=item.pk)
    return item


def booking_queryset(user):
    return GroupBookingProposal.objects.filter(
        Q(owner=user) | Q(participants__tenant=user)
    ).distinct()


def lifecycle_subject(user, identifier):
    for qs in (
        ApplicationProfile.objects.filter(applicant=user),
        ApplicationProfileVersion.objects.filter(profile__applicant=user),
        ApplicationAccessGrant.objects.filter(
            Q(applicant=user)
            | Q(
                recipient=user,
                property__owner=user,
                revoked_at__isnull=True,
                expires_at__gt=timezone.now(),
            )
        ),
        ReservationHold.objects.filter(
            Q(actor=user) | Q(property__owner=user), companybookingitem__isnull=True
        ),
        booking_queryset(user),
        case_queryset(user),
        PropertyDecisionFact.objects.filter(property__owner=user),
        RentalAvailabilityConfirmation.objects.filter(property__owner=user),
    ):
        item = qs.filter(id=identifier).first()
        if item:
            return item
    from ...models import RentalVerificationClaim
    from .common import staff_role

    claim = RentalVerificationClaim.objects.filter(id=identifier).first()
    if claim and staff_role(
        user,
        (
            {"kyc_reviewer"}
            if claim.subject_kind in {"identity", "student_enrollment"}
            else {"property_reviewer"}
        ),
    ):
        return claim
    return None
