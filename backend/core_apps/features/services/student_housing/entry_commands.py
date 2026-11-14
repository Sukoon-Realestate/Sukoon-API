"""Student command steps; typed adapters retain the HTTP boundary."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.features.student_models import SharedLivingAgreement
from core_apps.features.models import Lease
from core_apps.features.services.rental_lifecycle.access import property_for
from core_apps.features.services.rental_lifecycle.common import audit
from core_apps.features.services.student_housing import plans, publication
from core_apps.features.services.student_housing.access import plan_for, coordinator_for


def plan_action_post_apply(plan, revision, *, action, actor, data):
    if plan.status == "completed" and action not in {"link_lease", "check_in"}:
        from core_apps.features.services.rental_phase2 import RentalConflict

        raise RentalConflict(
            "This period is complete. Create another plan for new requirements.",
            code="plan_completed",
        )
    if action == "edit":
        return plans.save_plan(actor, data, plan)
    if action == "requirements":
        return plans.save_requirements(actor, plan, data)
    if action in {"review", "withdraw"}:
        return plans.review(actor, plan, data, withdraw=action == "withdraw")
    if action == "publish":
        return publication.publish(actor, plan, data)
    if action == "complete":
        if not coordinator_for(actor, plan):
            raise PermissionDenied(
                "Only the current coordinator can complete this plan."
            )
        plan.status = "completed"
    else:
        row = get_object_or_404(plan.participants, user=actor)
        from core_apps.features.services.student_housing.access import (
            participant_current,
        )

        if row.status == "withdrawn" or not participant_current(row):
            raise PermissionDenied("Current participation is required.")
        lease = get_object_or_404(Lease, id=data["lease_id"], tenant=actor)
        if action == "link_lease":
            row.lease = lease
            row.save(update_fields=["lease", "updated_at"])
        else:
            if lease.pk not in {row.lease_id, plan.current_lease_id}:
                raise ValidationError(
                    {
                        "lease_id": "Link your own rental to this plan before reporting an issue."
                    }
                )
            if lease.status not in {"active", "termination_pending", "ended"}:
                raise ValidationError(
                    {"lease_id": "A supported confirmed agreement is required."}
                )
            from core_apps.features.services.rental_lifecycle.cases import (
                open_system_case,
            )

            item = open_system_case(
                kind={
                    "access": "access_failure",
                    "wrong_space": "move_in_mismatch",
                    "missing_facility": "move_in_mismatch",
                }.get(data["kind"], data["kind"]),
                source_key=f"student-check-in:{actor.id}:{data['request_key']}",
                actor=actor,
                lease=lease,
                reason=data["note"],
                next_action="Review the student's report and coordinate the existing maintenance, change or support process.",
            )
            item.baseline = {**item.baseline, "academic_plan_id": str(plan.id)}
            item.save(update_fields=["baseline", "updated_at"])
    plan.revision += 1
    plan.save(update_fields=["revision", "status", "updated_at"])
    audit(plan, actor, "academic_plan." + action)
    return plan


def living_arrangement_post_load(*, actor, found):
    plan_for(actor, found.plan.id, lock=True)
    return SharedLivingAgreement.objects.select_for_update().get(pk=found.pk)


def student_offer_policy_post_load(*, actor, property_id):
    property_for(actor, property_id, owner=True, lock=True)
    return None
