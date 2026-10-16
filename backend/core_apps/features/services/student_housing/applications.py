"""Academic provenance on the shared rental application and agreement cycle."""

from rest_framework.exceptions import ValidationError
from ..planning import require_planning, check_revision
from ..rental_phase2 import RentalConflict
from .access import plan_for
from .plans import blockers
from .publication import preview


def context(user, data):
    if not data.get("academic_plan_id"):
        if data.get("source_housing_offer_id"):
            raise ValidationError(
                {"academic_plan_id": "An academic source needs its plan."}
            )
        return {}
    require_planning(user, "student_planning")
    plan = plan_for(user, data["academic_plan_id"], lock=True)
    if plan.group_id:
        raise ValidationError(
            {
                "academic_plan_id": "Use this group's canonical application and individual consent process."
            }
        )
    check_revision(plan.requirements_revision, data.get("academic_revision"))
    if blockers(plan):
        raise RentalConflict(
            "Review the current housing requirements first.", code="consent_required"
        )
    if data["desired_start"] != plan.starts_on or data["occupants"] != 1:
        raise ValidationError(
            {"desired_start": "Use the reviewed individual plan's dates and occupancy."}
        )
    source = None
    if data.get("source_housing_offer_id"):
        from ...planning_housing_views_parts.housing_request_action import (
            get_offer,
            offer_status,
        )

        source = get_offer(user, data["source_housing_offer_id"], lock=True)
        check_revision(source.revision, data.get("source_housing_offer_revision"))
        if (
            source.request.academic_plan_id != plan.pk
            or offer_status(source) != "selected_to_proceed"
            or str(source.property.id) != str(data["property_id"])
            or source.selection["offer_id"] != data["offer_id"]
            or source.selection["offer_revision"] != data["offer_revision"]
        ):
            raise RentalConflict(
                "Review the original housing response.", code="offer_changed"
            )
    snapshot = preview(plan)
    if source:
        snapshot.update(
            source_housing_offer_id=str(source.id),
            source_housing_offer_revision=source.revision,
            student_policy=source.student_policy_snapshot,
        )
    return {
        "academic_plan": plan,
        "academic_revision": plan.requirements_revision,
        "academic_snapshot": snapshot,
        "desired_end": plan.ends_on_exclusive,
        "source_housing_offer": source,
    }


def link_agreement(invitation, lease):
    from ...models import AcademicPlanParticipant, GroupBookingParticipant

    interest = invitation.interest
    if interest and interest.academic_plan_id:
        AcademicPlanParticipant.objects.filter(
            plan=interest.academic_plan, user=lease.tenant
        ).update(lease=lease)
    for participant in GroupBookingParticipant.objects.filter(
        invitation=invitation
    ).select_related("proposal__application"):
        process = participant.proposal.application
        if process.academic_plan_id:
            AcademicPlanParticipant.objects.filter(
                plan=process.academic_plan, user=lease.tenant
            ).update(lease=lease)
