"""Current responsibility, never group membership or employee debt."""

from ..models import PrivateAccessRevocation


def recipients(invoice):
    lease = invoice.lease
    denied = set(
        PrivateAccessRevocation.objects.filter(lease=lease).values_list(
            "user_id", flat=True
        )
    )

    def eligible(user):
        return user and user.is_active and user.is_verified and user.pk not in denied

    if not lease.renter_company_id:
        return [(lease.tenant, "payer")] if eligible(lease.tenant) else []
    from .company.tenancy_access import can_pay, roles

    item = lease.company_tenancy
    payer = item.payer_mandate.membership.user
    coordinator = item.coordinator
    selected = {}
    if eligible(payer) and can_pay(lease, payer):
        selected[payer.pk] = (payer, "payer")
    if eligible(coordinator) and "coordinator" in roles(item, coordinator):
        selected.setdefault(
            coordinator.pk,
            (coordinator, "coordinator" if selected else "authority_required"),
        )
    if not selected:
        for membership in lease.renter_company.memberships.filter(
            is_active=True, is_admin=True
        ).select_related("user"):
            if eligible(membership.user):
                selected[membership.user_id] = (membership.user, "authority_required")
    return list(selected.values())
