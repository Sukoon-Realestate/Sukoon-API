"""Compatibility entry points over canonical physical-unit/day allocations."""

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from ...models import ReservationHold
from .remember_mutation import RentalConflict


def reserve_inventory_days(lease, starts_on, ends_on_exclusive, expires_at):
    from ..rental_lifecycle.inventory import reserve_lease

    return reserve_lease(lease, starts_on, ends_on_exclusive, expires_at)


@transaction.atomic
def activate_inventory(lease):
    from core_apps.properties.models import Property
    from ..rental_lifecycle.inventory import hold_coverage

    if lease.renter_company_id:
        from ..company.tenancy_access import properties

        props = properties(lease.company_tenancy, lock=True)
    else:
        props = [Property.objects.select_for_update().get(pk=lease.property_id)]
    from core_apps.common.recovery import require_scope

    require_scope("inventory_commitments")
    from ..rental_lifecycle.habitability import assert_habitable

    for prop in props:
        assert_habitable(prop, lease.offer_snapshot)
    if not hold_coverage(lease):
        raise RentalConflict("The inventory hold has expired.", code="hold_expired")
    lease.inventory_day_locks.filter(kind="hold").update(
        kind="occupied", expires_at=None
    )
    ReservationHold.objects.filter(lease=lease).update(
        status="committed",
        expires_at=None,
        revision=F("revision") + 1,
        updated_at=timezone.now(),
    )
