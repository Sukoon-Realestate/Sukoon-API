"""Purpose-aware invoice page preparation; no provider or storage operations.

Only the selected page is materialized. Captured receipt identity and unresolved
status are correlated subqueries, so long payment histories are not prefetched.
Prepared facts live on these instances for this read only; commands continue to
read current authority under their original locks.
"""

from uuid import UUID

from django.db.models import Exists, OuterRef, Subquery, Prefetch
from ..models import (
    AccountSubscription,
    BoostCampaign,
    PaymentAttempt,
    SubscriptionPlan,
    StoreProduct,
)


def invoice_read_queryset(query):
    attempts = PaymentAttempt.objects.filter(invoice_id=OuterRef("pk"))
    captured = attempts.filter(payment_status="captured")
    if not captured.ordered:
        captured = captured.order_by("pk")
    return (
        query.select_related("organization", "fulfillment__case", "subscription")
        .annotate(
            read_receipt_id=Subquery(captured.values("pk")[:1]),
            read_unresolved=Exists(
                attempts.filter(payment_status__in=["created", "pending", "authorized"])
            ),
        )
        .prefetch_related("lines")
    )


def prepare_invoice_page(page):
    from core_apps.advertising.models import Advertisement

    page = list(page)
    receipts = {
        item.pk: item
        for item in PaymentAttempt.objects.filter(
            pk__in=[item.read_receipt_id for item in page if item.read_receipt_id]
        ).select_related("receipt", "paymob_payment", "store_intent")
    }
    from .store_payments import environment

    plans = {
        str(item.id): item
        for item in SubscriptionPlan.objects.filter(
            id__in={
                item.purchase_snapshot.get("id")
                for item in page
                if item.purpose == "subscription" and item.purchase_snapshot.get("id")
            }
        ).prefetch_related(
            Prefetch(
                "store_products",
                queryset=StoreProduct.objects.filter(
                    environment=environment(), active=True
                ).order_by("pk"),
                to_attr="prepared_store_products",
            )
        )
    }
    services = {}
    for purpose, model, key in (
        ("subscription", AccountSubscription, "id"),
        ("advertising", Advertisement, "subject_id"),
        ("promotion", BoostCampaign, "subject_id"),
    ):
        selected = [
            item for item in page if item.purpose == purpose and item.status == "paid"
        ]
        if not selected:
            continue
        if purpose == "subscription":
            services[purpose] = {
                str(item.invoice_id): item
                for item in model.objects.filter(invoice__in=selected)
            }
        else:
            services[purpose] = {
                str(item.id): item
                for item in model.objects.filter(
                    id__in={
                        item.purchase_snapshot.get(key)
                        for item in selected
                        if item.purchase_snapshot.get(key)
                    }
                )
            }
    for item in page:
        plan_id = item.purchase_snapshot.get("id")
        subject_id = item.purchase_snapshot.get("subject_id")
        plan_key = (
            str(UUID(str(plan_id)))
            if item.purpose == "subscription" and plan_id
            else None
        )
        subject_key = (
            str(UUID(str(subject_id)))
            if item.purpose in {"advertising", "promotion"}
            and item.status == "paid"
            and subject_id
            else None
        )
        state_key = str(item.pk) if item.purpose == "subscription" else subject_key
        item.prepared_billing = {
            "receipt": receipts.get(item.read_receipt_id),
            "unresolved": item.read_unresolved,
            "plan": plans.get(plan_key),
            "service": services.get(item.purpose, {}).get(state_key),
        }
    return page


__all__ = ["invoice_read_queryset", "prepare_invoice_page"]
