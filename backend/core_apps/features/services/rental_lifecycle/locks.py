"""One ordering for personal and portfolio company financial mutations."""

from core_apps.properties.models import Property
from ...models import Lease


def lock_financial_lease(lease):
    if lease.renter_company_id:

        from ..company.tenancy_access import lock_lease

        return lock_lease(lease)
    Property.objects.select_for_update().get(pk=lease.property_id)
    return Lease.objects.select_for_update().get(pk=lease.pk)


def require_personal_workflow(lease):
    from ..rental_phase2 import RentalConflict

    if lease.renter_company_id:
        raise RentalConflict(
            "Open the company tenancy to act on company responsibilities.",
            code="company_tenancy_required",
        )
