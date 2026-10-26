"""Private, durable notices for recorded execution steps; never replay a command."""

from django.http import Http404
from rest_framework.exceptions import NotFound, PermissionDenied
from ...planning_models import PlanningEvent
from .registry import adapter

EVENT_KIND = "advanced_execution_updated"


def workspace(plan, recipient):
    own = str(recipient.id)
    if any(
        leg.specification.get(
            "owner_id", leg.specification.get("terms", {}).get("owner_id")
        )
        == own
        for leg in plan.legs.all()
    ):
        return "owner"
    if plan.source_kind == "company_scenario":
        return "company"
    if plan.source_kind == "tender":
        from ...advanced_tender_models import PackageCandidate

        if PackageCandidate.objects.filter(
            id=plan.source_id, tender__request__academic_plan__isnull=False
        ).exists():
            return "student"
    if plan.source_kind == "transition":
        from ...models import AcademicPlanParticipant
        from ...transition_network_models import TransitionParticipant

        leases = TransitionParticipant.objects.filter(
            candidate__id=plan.source_id, user=recipient
        ).values("intent__lease_id")
        if AcademicPlanParticipant.objects.filter(
            user=recipient, lease_id__in=leases
        ).exists():
            return "student"
    return "individual"


def record(step):
    plan = step.execution
    recipients = plan.actors.filter(is_active=True)
    if step.leg_id:
        recipients = recipients.filter(
            id__in=set(step.leg.actor_ids)
            | set(plan.context.get("coordinator_ids", []))
        )
    if step.actor_id:
        recipients = recipients.exclude(pk=step.actor_id)
    for recipient in recipients:
        scope = workspace(plan, recipient)
        PlanningEvent.objects.get_or_create(
            recipient=recipient,
            event_key=f"advanced.execution:{step.id}",
            defaults={
                "destination": {
                    "action_type": "open_advanced_execution",
                    "event_kind": EVENT_KIND,
                    "target_id": str(plan.id),
                    "execution_step_id": str(step.id),
                    "execution_leg_id": str(step.leg.id) if step.leg_id else "",
                    "source_kind": plan.source_kind,
                    "revision": plan.revision,
                    "change_kind": step.kind,
                    "workspace": scope,
                    "company_id": (
                        plan.context.get("company_id", "") if scope == "company" else ""
                    ),
                    "schema_version": "1",
                }
            },
        )


def authorize(event):
    from .plans import get_plan

    data = event.destination
    plan = get_plan(event.recipient, data["target_id"])
    if data.get("event_kind") != EVENT_KIND or data.get("workspace") != workspace(
        plan, event.recipient
    ):
        raise NotFound()
    step = (
        plan.steps.select_related("leg")
        .filter(id=data.get("execution_step_id"))
        .first()
    )
    if not step or data.get("execution_leg_id", "") != (
        str(step.leg.id) if step.leg_id else ""
    ):
        raise NotFound()
    if data.get("company_id", "") != (
        plan.context.get("company_id", "") if data["workspace"] == "company" else ""
    ):
        raise NotFound()
    if step.leg_id and str(event.recipient.id) not in step.leg.actor_ids:
        if str(event.recipient.id) not in plan.context.get("coordinator_ids", []):
            raise NotFound()
        try:
            adapter(plan.source_kind).authorize(event.recipient, plan.source_id)
        except (NotFound, PermissionDenied, Http404):
            raise NotFound()
    return {
        "title": "تحديث تنفيذ السكن / Housing execution updated",
        "body": "راجع الحالة الحالية وسجل الجزء المعني لاستكمال الخطوة المطلوبة. / Review the current state and step history to continue the required action.",
    }
