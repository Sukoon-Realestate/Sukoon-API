"""Bounded, history-free personal financial list projections.

The compact_v1 projection is opt-in so existing clients retain their historical
full collections. Detail routes retain the original receipt/history contract.
No provider/storage calls or financial state changes occur here.
"""

from django.db.models import Q
from rest_framework.exceptions import ValidationError
from ..models import (
    OwnerPayable,
    RentalPayout,
    RefundRequest,
    RentalDispute,
    PrivateAccessRevocation,
)


def financial_list(actor, kind, *, workspace, lease_id=None):
    if kind in {"payables", "payouts"} and workspace != "owner":
        raise ValidationError({"workspace": "Must be owner."})
    if kind == "payables":
        query = OwnerPayable.objects.filter(
            Q(invoice__beneficiary=actor)
            | Q(invoice__beneficiary__isnull=True, lease__owner=actor)
        )
    elif kind == "payouts":
        query = RentalPayout.objects.filter(owner=actor)
    else:
        model = {"refunds": RefundRequest, "disputes": RentalDispute}[kind]
        query = model.objects.filter(
            **{"lease__owner" if workspace == "owner" else "lease__tenant": actor}
        )
        query = query.exclude(
            lease_id__in=PrivateAccessRevocation.objects.filter(user=actor).values(
                "lease_id"
            )
        )
    if lease_id:
        query = query.filter(lease__id=lease_id)
    relations = ["lease"]
    if kind == "payables":
        relations.append("invoice")
    elif kind == "refunds":
        relations.append("payment_attempt")
    fields = ["id", "lease__id", "revision"]
    fields += {
        "payables": [
            "payout_status",
            "net_minor",
            "invoice__id",
            "settlement_status",
            "blocking_reasons",
        ],
        "payouts": ["status", "amount_minor", "currency"],
        "refunds": ["status", "amount_minor", "payment_attempt__id", "purpose"],
        "disputes": ["status", "subject_kind", "subject_id"],
    }[kind]
    return query.select_related(*relations).only(*fields).order_by("-created_at", "-pk")


def financial_summary(item, kind):
    result = {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "status": item.payout_status if kind == "payables" else item.status,
    }
    if kind != "disputes":
        result["amount"] = {
            "amount_minor": item.net_minor if kind == "payables" else item.amount_minor,
            "currency": getattr(item, "currency", "EGP"),
            "exponent": 2,
        }
    if kind == "payables":
        result.update(
            invoice_id=str(item.invoice.id),
            settlement_status=item.settlement_status,
            blocking_reasons=item.blocking_reasons,
        )
    elif kind == "refunds":
        result.update(
            payment_attempt_id=str(item.payment_attempt.id), purpose=item.purpose
        )
    elif kind == "disputes":
        result.update(subject_kind=item.subject_kind, subject_id=str(item.subject_id))
    return result


__all__ = ["financial_list", "financial_summary"]
