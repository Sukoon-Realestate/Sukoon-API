"""Legal end dates do not imply returned possession or settled balances."""

from django.db import transaction
from django.utils import timezone

from ..models import BillingPeriod, Lease, RentalTimelineEvent


def accept_termination(change):
    lease = change.lease
    change.previous_terms = {**lease.terms, "ends_on_exclusive": str(lease.end_date)}
    lease.end_date = change.effective_on
    lease.status = Lease.Status.TERMINATION_PENDING
    lease.revision += 1
    lease.save(update_fields=["end_date", "status", "revision", "updated_at"])
    lease.billing_periods.filter(
        status=BillingPeriod.Status.SCHEDULED, start__gte=lease.end_date
    ).update(status=BillingPeriod.Status.CANCELLED)
    end_lease_if_due(lease)


def end_lease_if_due(lease):
    if (
        lease.status not in {Lease.Status.ACTIVE, Lease.Status.TERMINATION_PENDING}
        or lease.end_date > timezone.localdate()
    ):
        return False
    # Bill elapsed scheduled periods before ending; worker order cannot erase debt.
    from .rental_phase3 import issue_invoice

    for period in lease.billing_periods.filter(
        status=BillingPeriod.Status.SCHEDULED,
        start__lt=lease.end_date,
        issue_at__lte=timezone.now(),
    ).order_by("start", "pkid"):
        issue_invoice(period)
    lease.status = Lease.Status.ENDED
    if lease.occupancy_status == Lease.OccupancyStatus.OCCUPIED:
        lease.occupancy_status = Lease.OccupancyStatus.MOVE_OUT_PENDING
    lease.revision += 1
    lease.save(update_fields=["status", "occupancy_status", "revision", "updated_at"])
    lease.billing_periods.filter(
        status=BillingPeriod.Status.SCHEDULED, start__gte=lease.end_date
    ).update(status=BillingPeriod.Status.CANCELLED)
    RentalTimelineEvent.objects.create(
        lease=lease,
        kind="legally_ended",
        label="Agreement term ended",
        description="Possession return and financial closure require their separate confirmations.",
    )
    return True


def end_due_leases():
    changed = 0
    for identifier in Lease.objects.filter(
        legacy_read_only=False,
        status__in=[Lease.Status.ACTIVE, Lease.Status.TERMINATION_PENDING],
        end_date__lte=timezone.localdate(),
    ).values_list("pk", flat=True):
        with transaction.atomic():
            lease = Lease.objects.select_for_update().get(pk=identifier)
            changed += int(end_lease_if_due(lease))
    return changed
