"""Rental phase2: reserve inventory days."""

from datetime import timedelta
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ...models import RentalInventoryDayLock
from .remember_mutation import RentalConflict, _overlapping_accommodation


@transaction.atomic
def reserve_inventory_days(lease, starts_on, ends_on_exclusive, expires_at):
    from core_apps.properties.models import Property

    if ends_on_exclusive <= starts_on:
        raise ValidationError({"ends_on_exclusive": "Must be after starts_on."})
    now = timezone.now()
    # All offers in a property share this lock: a room and a bed in that room
    # must not be allocated concurrently under different offer IDs.
    Property.objects.select_for_update().get(pk=lease.property_id)
    RentalInventoryDayLock.objects.filter(
        property_id=lease.property_id,
        kind=RentalInventoryDayLock.Kind.HOLD,
        expires_at__lte=now,
    ).delete()
    conflicts = (
        RentalInventoryDayLock.objects.filter(
            property_id=lease.property_id,
            stay_on__gte=starts_on,
            stay_on__lt=ends_on_exclusive,
        )
        .exclude(lease=lease)
        .select_related("lease")
    )
    for occupied in conflicts:
        if occupied.offer_id == lease.offer_id or _overlapping_accommodation(
            lease.offer_snapshot,
            occupied.lease.offer_snapshot if occupied.lease else None,
        ):
            raise RentalConflict(
                "The accommodation is no longer available for those dates.",
                code="offer_unavailable",
            )
    days = []
    current = starts_on
    while current < ends_on_exclusive:
        days.append(
            RentalInventoryDayLock(
                property=lease.property,
                offer_id=lease.offer_id,
                stay_on=current,
                kind=RentalInventoryDayLock.Kind.HOLD,
                lease=lease,
                expires_at=expires_at,
            )
        )
        current += timedelta(days=1)
    try:
        with transaction.atomic():
            RentalInventoryDayLock.objects.bulk_create(days)
    except IntegrityError:
        raise RentalConflict(
            "The accommodation is no longer available for those dates.",
            code="offer_unavailable",
        )


def activate_inventory(lease):
    holds = RentalInventoryDayLock.objects.filter(
        lease=lease,
        kind=RentalInventoryDayLock.Kind.HOLD,
        expires_at__gt=timezone.now(),
    )
    if holds.count() != (lease.end_date - lease.start_date).days:
        raise RentalConflict("The inventory hold has expired.", code="hold_expired")
    holds.update(kind=RentalInventoryDayLock.Kind.OCCUPIED, expires_at=None)
