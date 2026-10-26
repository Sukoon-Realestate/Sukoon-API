"""Owner receipts follow the original payout even if the property's owner changes."""

from rest_framework.exceptions import NotFound
from ..models import RentalPayout
from ..planning_models import PlanningEvent


def record(payout, action):
    PlanningEvent.objects.get_or_create(
        recipient=payout.owner,
        event_key=f"payout:{payout.id}:{payout.revision}:{action}",
        defaults={
            "destination": {
                "action_type": "open_rental_payout",
                "event_kind": "payout_updated",
                "target_id": str(payout.id),
                "payout_id": str(payout.id),
                "lease_id": str(payout.lease.id),
                "workspace": "owner",
                "revision": payout.revision,
                "change": action,
            }
        },
    )


def authorize(event):
    data = event.destination
    if (
        data.get("workspace") != "owner"
        or data.get("event_kind") != "payout_updated"
        or data.get("target_id") != data.get("payout_id")
        or not RentalPayout.objects.filter(
            id=data.get("payout_id"),
            owner=event.recipient,
            lease__id=data.get("lease_id"),
        ).exists()
    ):
        raise NotFound()
    return {
        "title": "تحديث مستحقاتك / Payout update",
        "body": "راجع الحالة الحالية للتحويل وسجل تغيّرها. / Review the current transfer status and its history.",
    }
