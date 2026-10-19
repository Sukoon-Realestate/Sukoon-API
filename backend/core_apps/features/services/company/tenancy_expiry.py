"""Expire every unit of a company agreement under the canonical lock order."""

from django.db import transaction
from django.utils import timezone
from ...models import CompanyTenancy, CompanyBudgetReservation, ReservationHold
from ..rental_lifecycle.inventory import unresolved_payment
from ..rental_lifecycle.cases import open_system_case
from . import tenancy_access as access


@transaction.atomic
def expire(item, now=None):
    now = now or timezone.now()
    lease = access.lock_lease(item.lease)
    item = CompanyTenancy.objects.select_for_update().get(pk=item.pk)
    item.lease = lease
    if (
        lease.status not in {"draft", "pending_signatures", "signed"}
        or not lease.hold_expires_at
        or lease.hold_expires_at > now
    ):
        return False
    # A pending signature may already have bound a party at the provider.
    # A timeout is not proof of failure and must not authorize a new allocation.
    if (
        unresolved_payment(lease)
        or lease.signing_sessions.filter(
            status__in=["pending", "completed", "review_required"]
        ).exists()
    ):
        hold = ReservationHold.objects.get(lease=lease)
        if hold.status != "reconciliation_pending":
            hold.status = "reconciliation_pending"
            hold.revision += 1
            hold.save()
        open_system_case(
            kind="company_tenancy_review",
            source_key=f"company-expiry:{lease.id}",
            lease=lease,
            hold=hold,
            reason="An expired company hold has unresolved signature or payment evidence.",
            next_action="Reconcile every original provider instruction before an authorized release or continuation.",
        )
        return False
    lease.inventory_day_locks.filter(kind="hold").delete()
    ReservationHold.objects.filter(lease=lease).update(
        status="expired", released_at=now
    )
    CompanyBudgetReservation.objects.filter(
        item=item.preparation.booking, status="reserved"
    ).update(status="released")
    lease.status = "expired"
    access.changed(item, None, "company_agreement_expired")
    return True


def expire_due(now=None):
    now = now or timezone.now()
    from core_apps.common.recovery import require_scope

    require_scope("company_authority")
    count = 0
    for item in CompanyTenancy.objects.filter(
        lease__hold_expires_at__lte=now,
        lease__status__in=["draft", "pending_signatures", "signed"],
    ).order_by("id")[:100]:
        count += int(expire(item, now))
    return count
