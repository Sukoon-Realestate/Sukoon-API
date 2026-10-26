"""Recipient context and fresh access for durable appointment events."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from ..models import PropertyVisit
from .viewing_access import can_read, group_process


def recipient_scope(visit, recipient_id):
    if visit.property.owner_id == recipient_id:
        return "owner"
    if visit.company_id:
        return "company"
    if (
        visit.academic_plan_id
        or visit.context_kind in {"student", "group"}
        or group_process(visit)
    ):
        return "student"
    return visit.renter_workspace


def authorize(event):
    visit = get_object_or_404(PropertyVisit, id=event.destination.get("visit_id"))
    if (
        not can_read(visit, event.recipient)
        or event.destination.get("target_id") != str(visit.id)
        or event.destination.get("action_type") != "view_visit"
    ):
        raise NotFound()
    scope = recipient_scope(visit, event.recipient_id)
    # Existing queued events retain their identity and acquire the authoritative
    # recipient context when sent. Their older revision is history, not authority.
    event.destination.update(workspace=scope, schema_version="1")
    return {
        "title": "تحديث المعاينة / Viewing update",
        "body": "افتح المعاينة لمراجعة حالتها الحالية وسجل التغيير. / Open the viewing for its current state and change history.",
    }
