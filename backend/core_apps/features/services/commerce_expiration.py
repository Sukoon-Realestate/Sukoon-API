"""Observe service expiry once, atomically with its durable notification."""

from django.db import transaction
from django.utils import timezone

from core_apps.advertising.models import Advertisement
from ..models import AccountSubscription, BillingSourceLink, BoostCampaign
from .commerce_expiration_notifications import record


MODELS = {
    "subscription": AccountSubscription,
    "promotion": BoostCampaign,
    "advertising": Advertisement,
}


def due(kind, now):
    query = MODELS[kind].objects.filter(ends_at__lte=now)
    if kind == "subscription":
        # Store lifecycle/renewals remain outside this round.
        return query.filter(
            expiration_processed_at__isnull=True, store_platform="", store_status=""
        )
    states = ["active", "paused"] if kind == "promotion" else ["active"]
    return query.filter(status__in=states)


def expire(*, kinds=None, limit=100, now=None):
    now = now or timezone.now()
    processed = 0
    for kind in kinds or MODELS:
        identities = list(
            due(kind, now)
            .order_by("ends_at", "pk")
            .values_list("pk", flat=True)[:limit]
        )
        for identity in identities:
            with transaction.atomic():
                item = (
                    due(kind, now)
                    .select_for_update(skip_locked=True)
                    .filter(pk=identity)
                    .first()
                )
                if item is None:
                    continue
                fields = ["expiration_processed_at", "updated_at"]
                first = item.expiration_processed_at is None
                item.expiration_processed_at = item.expiration_processed_at or now
                if kind != "subscription":
                    item.status = "expired"
                    fields.append("status")
                item.save(update_fields=fields)
                if first:
                    invoice = (
                        item.invoice
                        if kind == "subscription"
                        else invoice_for(kind, item)
                    )
                    record(kind, item, invoice)
                processed += 1
    return processed


def invoice_for(kind, item):
    link = (
        BillingSourceLink.objects.select_related("invoice")
        .filter(source_kind=kind, source_id=item.id, invoice__status="paid")
        .first()
    )
    return link.invoice if link else None
