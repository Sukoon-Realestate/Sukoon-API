"""Recipient-scoped corporate updates; historical notices open the current tenancy."""

from rest_framework.exceptions import NotFound
from ...planning_models import PlanningEvent
from . import tenancy_access as access


def workspace(item, user):
    roles = access.roles(item, user)
    if not roles:
        return None
    return "owner" if roles & {"owner", "new_owner"} else "company"


def record(item, people, action):
    from core_apps.users.models import User

    for user in User.objects.filter(pk__in=people, is_active=True):
        scope = workspace(item, user)
        if not scope:
            continue
        PlanningEvent.objects.get_or_create(
            recipient=user,
            event_key=f"company.tenancy:{item.id}:{item.revision}",
            defaults={
                "destination": {
                    "action_type": "open_company_tenancy",
                    "target_id": str(item.id),
                    "company_id": str(item.lease.renter_company.id),
                    "lease_id": str(item.lease.id),
                    "workspace": scope,
                    "schema_version": "1",
                    "revision": item.revision,
                    "event_kind": "company_tenancy_updated",
                    "change_kind": action,
                }
            },
        )


def authorize(event):
    item = access.get(event.recipient, event.destination["target_id"])
    data = event.destination
    # Preserve already-queued legacy notices; all new events carry explicit binding.
    if data.get("event_kind") == "company_tenancy_updated" and (
        data.get("company_id") != str(item.lease.renter_company.id)
        or data.get("lease_id") != str(item.lease.id)
        or data.get("workspace") != workspace(item, event.recipient)
    ):
        raise NotFound()
    return {
        "title": "تحديث سكن الشركة / Company tenancy updated",
        "body": "راجع الحالة الحالية والمهمة المتاحة لك وسجل التغيير. / Review the current state, your task and its history.",
    }


def history(item, user):
    return [
        {
            "revision": event.destination.get("revision", 0),
            "action": event.destination.get("change_kind", "company_tenancy_updated"),
            "occurred_at": event.created_at.isoformat(),
        }
        for event in PlanningEvent.objects.filter(
            recipient=user,
            destination__target_id=str(item.id),
            destination__event_kind="company_tenancy_updated",
        ).order_by("created_at", "pk")
    ]
