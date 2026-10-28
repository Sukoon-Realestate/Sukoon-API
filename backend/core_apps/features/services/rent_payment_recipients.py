"""Current responsibility, never group membership or employee debt."""

from ..models import PrivateAccessRevocation


from .company.role_context import system_context


@system_context()
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
    # Invoice notices belong only to the current delegated payer. An admin or
    # coordinator must never receive a financial destination as a fallback.
    return [(payer, "payer")] if eligible(payer) and can_pay(lease, payer) else []
