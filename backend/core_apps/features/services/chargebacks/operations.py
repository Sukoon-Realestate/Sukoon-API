"""Independent approval of evidenced excess; operators cannot manufacture bank facts."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from ...models import RentalChargeback, RefundRequest
from ..financial_authority import require_financial_actor
from ..rental_lifecycle.locks import lock_financial_lease
from ..rental_lifecycle.common import command, require_revision, audit
from ..rental_phase2 import RentalConflict
from .projection import payload


def require_operator(user, lease, *, lock=False):
    current = require_financial_actor(
        user,
        {"financial_approver", "refund_operator", "psp_reconciliation"},
        "chargeback.review",
        lock=lock,
    )
    if current.pk in {lease.owner_id, lease.tenant_id} or (
        lease.renter_company_id
        and lease.renter_company.memberships.filter(user=current).exists()
    ):
        raise PermissionDenied(
            "An independent financial operator must review this chargeback."
        )
    return current


def detail(user, identity):
    require_financial_actor(
        user,
        {"financial_approver", "refund_operator", "psp_reconciliation"},
        "chargeback.review",
    )
    item = get_object_or_404(
        RentalChargeback.objects.select_related(
            "payment_attempt__invoice__lease", "opening_event"
        ),
        id=identity,
    )
    require_operator(user, item.payment_attempt.invoice.lease)
    return item


def approve_refund(user, identity, data):
    def authorize():
        item = detail(user, identity)
        require_financial_actor(
            user,
            {"financial_approver", "refund_operator"},
            "chargeback.approve_refund",
            lock=True,
        )
        lease = lock_financial_lease(item.payment_attempt.invoice.lease)
        require_operator(user, lease, lock=True)
        return RentalChargeback.objects.select_for_update().get(pk=item.pk)

    def execute(item):
        require_financial_actor(
            user,
            {"financial_approver", "refund_operator"},
            "chargeback.approve_refund",
            lock=True,
        )
        require_revision(item, data.get("expected_revision"))
        reason = str(data.get("reason", "")).strip()
        if not reason or len(reason) > 2000:
            raise ValidationError(
                {
                    "reason": "Explain the independent refund approval in at most 2000 characters."
                }
            )
        from .refunds import source

        refund = get_object_or_404(
            RefundRequest.objects.select_for_update(),
            id=data.get("refund_id"),
            purpose="chargeback_excess",
        )
        row, _ = source(refund)
        if row.chargeback_id != item.pk:
            raise PermissionDenied("The refund must belong to this exact chargeback.")
        if refund.status != "requested":
            raise RentalConflict(
                "Only the outstanding original refund may be approved."
            )
        refund.status, refund.approved_by = "approved", user
        refund.revision += 1
        refund.save()
        item.revision += 1
        item.save()
        audit(
            item,
            user,
            "chargeback.excess_refund_approved",
            reason,
            {"refund_id": str(refund.id)},
        )
        return item, payload(item), 200

    return command(
        user=user,
        operation=f"chargeback.approve_excess.{identity}",
        data=data,
        authorize=authorize,
        execute=execute,
    )
