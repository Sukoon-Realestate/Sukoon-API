"""Private student events, committed with their command and authorized on retry."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound

from ...planning_models import PlanningEvent
from ...student_models import SharedLivingAgreement
from .access import plan_for

EVENT_KINDS = {"student_plan_changed", "student_arrangement_changed"}


def record(item, actor, operation):
    arrangement = isinstance(item, SharedLivingAgreement)
    plan = item.plan if arrangement else item
    # Private check-in reports and lease links follow their own case/rental path.
    change = operation.split(".")[1]
    if not arrangement and change not in {
        "create",
        "edit",
        "requirements",
        "review",
        "withdraw",
        "publish",
        "complete",
    }:
        return
    members = (
        {
            row.user_id: row
            for row in plan.group.memberships.filter(
                status="active",
                user__is_active=True,
                joined_revision__lte=plan.access_group_revision,
            ).select_related("user")
        }
        if plan.group_id and plan.group.status == "active"
        else {}
    )
    removed = getattr(plan, "_student_removed_recipient_ids", set())
    recipients = (
        set(
            plan.participants.exclude(status="withdrawn").values_list(
                "user_id", flat=True
            )
        )
        | removed
    )
    if arrangement:
        recipients &= {
            pk
            for pk, row in members.items()
            if str(row.user.id) in item.participant_ids
        }
    else:
        recipients.update(pk for pk, row in members.items() if row.role == "admin")
    for identity in recipients - {actor.pk}:
        member = members.get(identity)
        if member is None:
            continue
        PlanningEvent.objects.get_or_create(
            recipient_id=identity,
            event_key=f"student.{operation}:{item.id}:{item.revision}",
            defaults={
                "destination": {
                    "schema_version": "1",
                    "workspace": "student",
                    "action_type": (
                        "open_student_arrangement"
                        if arrangement
                        else "open_student_plan"
                    ),
                    "event_kind": (
                        "student_arrangement_changed"
                        if arrangement
                        else "student_plan_changed"
                    ),
                    "target_id": str(item.id),
                    "academic_plan_id": str(plan.id),
                    "resource_revision": item.revision,
                    "content_version": (
                        item.terms_revision
                        if arrangement
                        else plan.requirements_revision
                    ),
                    "recipient_membership_revision": member.joined_revision,
                    "recipient_removed": identity in removed,
                    "change_kind": change,
                }
            },
        )


def authorize(user, destination):
    kind = destination.get("event_kind")
    if kind not in EVENT_KINDS or destination.get("workspace") != "student":
        raise NotFound()
    plan = plan_for(user, destination.get("academic_plan_id"))
    if (
        not plan.group_id
        or not plan.group.memberships.filter(
            user=user,
            status="active",
            joined_revision=destination.get("recipient_membership_revision"),
            joined_revision__lte=plan.access_group_revision,
        ).exists()
    ):
        raise NotFound()
    arrangement = kind == "student_arrangement_changed"
    if arrangement:
        item = get_object_or_404(
            SharedLivingAgreement, id=destination.get("target_id"), plan=plan
        )
        if str(user.id) not in item.participant_ids:
            raise NotFound()
    elif str(plan.id) != destination.get("target_id") or not (
        plan.participants.filter(user=user).exclude(status="withdrawn").exists()
        or destination.get("recipient_removed") is True
        and plan.participants.filter(user=user, status="withdrawn").exists()
        or plan.group.memberships.filter(
            user=user, status="active", role="admin"
        ).exists()
    ):
        raise NotFound()
    expected = "open_student_arrangement" if arrangement else "open_student_plan"
    if destination.get("action_type") != expected:
        raise NotFound()
    return {
        "title": (
            "تحديث ترتيبات الطلاب / Student arrangements updated"
            if arrangement
            else "تحديث خطة الطلاب / Student plan updated"
        ),
        "body": "افتح الحالة الحالية وسجل التغيير. الموافقات تخص النسخة التي راجعها كل مشارك. / Open the current state and change history. Each participant approves only the version they reviewed.",
    }
