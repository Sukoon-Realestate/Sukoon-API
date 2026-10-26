"""Public planning changes only; never disclose a participant's private response."""

from django.http import Http404
from rest_framework.exceptions import NotFound
from ...planning_models import PlanningEvent
from .access import lab_for

EVENT = "living_lab_updated"
ACTION = "open_living_lab"
CHANGES = {"created", "updated", "result_updated", "agreed", "handoff", "closed"}


def record(lab, actor, operation):
    action = operation.split(":", 1)[0].split(".")[-1]
    if action == "respond" and lab.status != "agreed":
        return  # Another participant's accept/reject remains private.
    if action in {"requirements", "disclose"} and lab.status != "needs_revision":
        return
    change = {
        "create": "created",
        "scenario": "created",
        "run": "result_updated",
        "respond": "agreed",
        "prepare_cost_proposal": "handoff",
        "prepare_application": "handoff",
        "prepare_tender": "handoff",
        "close": "closed",
    }.get(action, "updated")
    for member in lab.group.memberships.filter(status="active").select_related("user"):
        if member.user_id == actor.pk:
            continue
        try:
            lab_for(member.user, lab.id)
        except (NotFound, Http404):
            continue
        PlanningEvent.objects.get_or_create(
            recipient=member.user,
            event_key=f"living-lab:{lab.id}:{lab.revision}:{change}",
            defaults={
                "destination": {
                    "schema_version": "1",
                    "action_type": ACTION,
                    "event_kind": EVENT,
                    "target_id": str(lab.id),
                    "group_id": str(lab.group.id),
                    "revision": lab.revision,
                    "change": change,
                    "workspace": "student",
                }
            },
        )


def authorize(event):
    data = event.destination
    if (
        data.get("action_type") != ACTION
        or data.get("event_kind") != EVENT
        or (data.get("workspace") != "student" or data.get("change") not in CHANGES)
    ):
        raise NotFound()
    lab = lab_for(event.recipient, data.get("target_id"))
    if data.get("group_id") != str(lab.group.id):
        raise NotFound()
    return {
        "title": "تحديث مختبر السكن / Living lab updated",
        "body": "راجع الحالة الحالية والتغييرات وخطوة المتابعة. موافقات الإيجار والدفع مستقلة. / Review the current state, changes and next step. Rental and payment approvals remain separate.",
    }


def public_history(lab):
    # Called only after lab_for has checked the viewer's exact membership period.
    rows = (
        PlanningEvent.objects.filter(
            destination__action_type=ACTION,
            destination__target_id=str(lab.id),
        )
        .order_by("-created_at")
        .values("destination", "created_at")[:200]
    )
    result, seen = [], set()
    for row in rows:
        data = row["destination"]
        key = (data.get("revision"), data.get("change"))
        if key in seen or key[1] not in CHANGES:
            continue
        seen.add(key)
        result.append(
            {
                "revision": key[0],
                "change": key[1],
                "created_at": row["created_at"].isoformat(),
            }
        )
    return result
