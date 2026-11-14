"""Current financial reads and locks, independent of HTTP requests."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from core_apps.features.models import Lease, PaymentAttempt, RentInvoice
from core_apps.features.services.company.tenancy_access import financial_read
from core_apps.features.services.rental_lifecycle.locks import (
    lock_financial_lease as _lock_lease,
)
from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import RefundRequest
from core_apps.features.models import PrivateAccessRevocation
from core_apps.features.providers import (
    require_rental_provider,
    require_verified_rental_account,
)


def rental_invoice_for(actor, invoice_id, lock=False):
    queryset = RentInvoice.objects.select_related(
        "lease", "lease__property", "billing_period"
    )
    if lock:
        candidate = get_object_or_404(queryset, id=invoice_id)
        if candidate.lease_id is None:
            raise NotFound()
        _lock_lease(candidate.lease)
        queryset = queryset.select_for_update(of=("self",))
    invoice = get_object_or_404(queryset, id=invoice_id)
    if invoice.lease_id is None or (
        invoice.beneficiary_id != actor.pk
        and (not financial_read(invoice.lease, actor))
    ):
        raise NotFound()
    return invoice


def payment_attempt_for(actor, attempt_id, lock=False, allow_original_payer=False):
    queryset = PaymentAttempt.objects.select_related("invoice__lease", "quote")
    if lock:
        candidate = get_object_or_404(queryset, id=attempt_id)
        if candidate.invoice.lease_id is not None:
            _lock_lease(candidate.invoice.lease)
        queryset = queryset.select_for_update(of=("self",))
    attempt = get_object_or_404(queryset, id=attempt_id)
    if attempt.invoice.lease_id is None:
        from ..services.billing_invoices import authorized_invoice

        authorized_invoice(actor, attempt.invoice.id)
        return attempt
    if allow_original_payer and attempt.payer_id == actor.pk:
        return attempt
    if attempt.invoice.beneficiary_id != actor.pk and (
        not financial_read(attempt.invoice.lease, actor)
    ):
        raise NotFound()
    return attempt


def refund_for(actor, refund_id, allow_operations=False, lock=False):
    queryset = RefundRequest.objects.select_related(
        "lease__owner", "lease__tenant", "payment_attempt__invoice"
    )
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    item = get_object_or_404(queryset, id=refund_id)
    from ..models import PrivateAccessRevocation

    if PrivateAccessRevocation.objects.filter(lease=item.lease, user=actor).exists():
        raise NotFound()
    from ..services.rental_lifecycle.common import staff_role

    operator = allow_operations and staff_role(
        actor,
        {
            StaffProfile.RoleName.REFUND_OPERATOR,
            StaffProfile.RoleName.FINANCIAL_APPROVER,
        },
    )
    if actor not in (item.lease.owner, item.lease.tenant) and (not operator):
        raise NotFound()
    return item


def personal_financial_lease(
    actor, lease_id, lock=False, *, provider_required=False, write=False
):
    if write:
        (
            require_rental_provider
            if provider_required
            else require_verified_rental_account
        )(actor)
    queryset = Lease.objects.select_related("owner", "tenant", "property")
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    lease = get_object_or_404(queryset, id=lease_id)
    from ..services.rental_lifecycle.locks import require_personal_workflow

    require_personal_workflow(lease)
    if actor not in (lease.owner, lease.tenant):
        raise NotFound()
    if PrivateAccessRevocation.objects.filter(lease=lease, user=actor).exists():
        raise NotFound()
    return lease


__all__ = [
    "payment_attempt_for",
    "personal_financial_lease",
    "refund_for",
    "rental_invoice_for",
]
