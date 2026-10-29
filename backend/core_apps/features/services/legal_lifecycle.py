"""Legal end dates do not imply returned possession or settled balances."""

from django.db import transaction
from django.utils import timezone

from ..models import BillingPeriod, Lease, RentalChange, RentalTimelineEvent


@transaction.atomic
def accept_termination(change):
    lease = change.lease
    if not lease.renter_company_id:
        from .termination_notice import fail, require_application

        lease = Lease.objects.select_for_update().get(pk=change.lease_id)
        locked = RentalChange.objects.select_for_update().get(pk=change.pk)
        locked.lease = lease
        if (
            locked.termination_notice_snapshot != change.termination_notice_snapshot
            or locked.approvals != change.approvals
            or locked.effective_on != change.effective_on
            or locked.content_revision != change.content_revision
            or locked.kind != change.kind
        ):
            fail("termination_notice_review_required")
        require_application(locked)
        change.lease = lease
    change.previous_terms = {**(lease.terms if isinstance(lease.terms, dict) else {}), "ends_on_exclusive": str(lease.end_date)}
    lease.end_date = change.effective_on
    lease.status = Lease.Status.TERMINATION_PENDING
    lease.revision += 1
    lease.save(update_fields=["end_date", "status", "revision", "updated_at"])
    lease.billing_periods.filter(
        status=BillingPeriod.Status.SCHEDULED, start__gte=lease.end_date
    ).update(status=BillingPeriod.Status.CANCELLED)
    end_lease_if_due(lease)


def end_lease_if_due(lease):
    from .termination_notice import today

    civil_day = timezone.localdate() if lease.renter_company_id else today()
    if (
        lease.status not in {Lease.Status.ACTIVE, Lease.Status.TERMINATION_PENDING}
        or lease.end_date > civil_day
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
    if lease.renter_company_id:
        from .company.tenancy_access import notify

        notify(lease.company_tenancy)
    return True


def end_due_leases():
    changed = 0
    for identifier in Lease.objects.filter(
        legacy_read_only=False,
        status__in=[Lease.Status.ACTIVE, Lease.Status.TERMINATION_PENDING],
        end_date__lte=timezone.localdate(),
    ).values_list("pk", flat=True):
        with transaction.atomic():
            lease = Lease.objects.get(pk=identifier)

            from .rental_lifecycle.locks import lock_financial_lease

            lease = lock_financial_lease(lease)
            changed += int(end_lease_if_due(lease))
    return changed
