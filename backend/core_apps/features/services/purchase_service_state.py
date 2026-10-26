"""Current service access is separate from the immutable purchase receipt."""

from django.utils import timezone


def service_state(invoice):
    if invoice.status != "paid":
        return None
    if invoice.purpose == "subscription":
        from ..models import AccountSubscription
        from .billing_catalog import subscription_status

        item = AccountSubscription.objects.filter(invoice=invoice).first()
        if item is None:
            return None
        status = subscription_status(item)
        end = item.grace_ends_at if status == "grace" else item.ends_at
    elif invoice.purpose == "advertising":
        from core_apps.advertising.models import Advertisement
        from core_apps.advertising.services_parts.ensure_media_persisted import (
            effective_status,
        )

        item = Advertisement.objects.filter(
            id=invoice.purchase_snapshot.get("subject_id")
        ).first()
        if item is None:
            return None
        status = effective_status(item)
        end = item.ends_at
    elif invoice.purpose == "promotion":
        from ..models import BoostCampaign

        item = BoostCampaign.objects.filter(
            id=invoice.purchase_snapshot.get("subject_id")
        ).first()
        if item is None:
            return None
        status = item.status
        if status in {"active", "paused"} and item.ends_at <= timezone.now():
            status = "expired"
        end = item.ends_at
    else:
        return None
    return {
        "id": str(item.id),
        "status": status,
        "starts_at": item.starts_at.isoformat() if item.starts_at else None,
        "ends_at": end.isoformat() if end else None,
    }
