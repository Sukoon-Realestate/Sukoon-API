"""Consented public projection in the existing housing-demand marketplace."""

from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from ...planning_models import HousingRequest
from ..planning import require_planning
from ..rental_phase2 import RentalConflict, fingerprint
from ..rental_lifecycle.common import audit
from .access import coordinator_for, participant_current
from .plans import blockers, current_digest


def disclosed_requirements(row):
    value = {}
    if "campuses" in row.owner_disclosures:
        value["campus_ids"] = row.requirements.get("campus_ids", [])
        value["internship_destination"] = row.requirements.get(
            "internship_destination", ""
        )
    if "affordability" in row.owner_disclosures:
        for key in ("budget_min", "budget_max"):
            value[key] = row.requirements.get(key)
    if "study_requirements" in row.owner_disclosures:
        for key in (
            "study_space",
            "internet",
            "commute_mode",
            "max_commute_minutes",
            "summer_intention",
            "admission_contingency",
        ):
            value[key] = row.requirements.get(key)
    return value


def preview(plan):
    from .profiles import requirements_payload

    # Owners receive anonymous requirement rows, never the group roster or documents.
    value = {
        "academic_plan_id": str(plan.id),
        "academic_revision": plan.requirements_revision,
        "label": plan.label,
        "period_kind": plan.period_kind,
        "starts_on": str(plan.starts_on),
        "ends_on_exclusive": str(plan.ends_on_exclusive),
        "budget_basis": plan.budget_basis,
        "currency": "EGP",
        "price_period": "monthly",
        "intended_occupants": plan.participants.exclude(status="withdrawn").count(),
        "budget_min": plan.criteria.get("budget_min"),
        "budget_max": plan.criteria.get("budget_max"),
        "shared_requirements": requirements_payload(plan.requirements),
        "participant_requirements": [
            requirements_payload(disclosed_requirements(row))
            for row in plan.participants.exclude(status="withdrawn").order_by(
                "user__id"
            )
        ],
        "commitment": "requirements_only",
    }
    return {**value, "preview_digest": fingerprint(value)}


def request_current(item):
    if not item.academic_plan_id:
        return True
    plan = item.academic_plan
    return plan.requirements_revision == item.academic_revision and not blockers(plan)


def publish(user, plan, data):
    require_planning(user, "housing_requests")
    if not coordinator_for(user, plan):
        raise PermissionDenied(
            "Only the plan coordinator may publish reviewed requirements."
        )
    if data["consent"] is not True or data["digest"] != preview(plan)["preview_digest"]:
        raise RentalConflict(
            "Review exactly what owners will see.", code="document_changed"
        )
    reasons = blockers(plan)
    if reasons:
        raise RentalConflict(
            {
                "message": "Participants must review the current requirements.",
                "code": reasons[0],
            },
            code=reasons[0],
        )
    if plan.housing_requests.filter(
        academic_revision=plan.requirements_revision
    ).exists():
        raise RentalConflict(
            "This plan revision already has a housing request.", code="request_exists"
        )
    if (
        HousingRequest.objects.filter(
            user=user, status__in=["published", "paused"], expires_at__gt=timezone.now()
        ).count()
        >= settings.PLANNING_MAX_LIVE_REQUESTS
    ):
        raise RentalConflict("Close an existing request first.", code="request_limit")
    HousingRequest.objects.create(
        user=user,
        title=plan.label,
        criteria=plan.criteria,
        expires_at=timezone.now() + timedelta(days=settings.PLANNING_REQUEST_TTL_DAYS),
        academic_plan=plan,
        academic_revision=plan.requirements_revision,
        academic_snapshot=preview(plan),
    )
    plan.revision += 1
    plan.save(update_fields=["revision", "updated_at"])
    audit(
        plan, user, "academic_plan.published", metadata={"digest": current_digest(plan)}
    )
    return plan


def participant_can_read(user, item):
    if not item.academic_plan_id:
        return False
    from .access import plan_for
    from rest_framework.exceptions import NotFound

    try:
        plan_for(user, item.academic_plan.id)
    except NotFound:
        return False
    return item.academic_plan.participants.filter(user=user).exists()
