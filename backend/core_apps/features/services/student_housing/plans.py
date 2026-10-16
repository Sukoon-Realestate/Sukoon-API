import json
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from ...student_models import (
    AcademicHousingPlan,
    AcademicPlanParticipant,
    AcademicRequirementRevision,
    Campus,
)
from ...models import Lease, RentalConsentRecord
from ...planning_models import HousingGroup
from ..planning import criteria, criteria_payload, money, check_revision
from ..commands import money_minor
from ..rental_phase2 import RentalConflict, fingerprint
from ..rental_lifecycle.common import audit
from .access import coordinator_for, participant_current, plan_for


def json_value(value):
    return json.loads(json.dumps(value, default=str))


def validate_destinations(requirements):
    ids = requirements.get("campus_ids", [])
    if len(set(map(str, ids))) != len(ids) or Campus.objects.filter(
        id__in=ids, active=True, university__active=True
    ).count() != len(ids):
        raise ValidationError({"campus_ids": "Select current campus catalog entries."})
    return json_value(requirements)


def snapshot(plan):
    return {
        "id": str(plan.id),
        "revision": plan.requirements_revision,
        "group_id": str(plan.group.id) if plan.group_id else None,
        "roster_revision": plan.roster_revision,
        "access_group_revision": plan.access_group_revision,
        "label": plan.label,
        "period_kind": plan.period_kind,
        "starts_on": str(plan.starts_on),
        "ends_on_exclusive": str(plan.ends_on_exclusive),
        "budget_basis": plan.budget_basis,
        "criteria": plan.criteria,
        "requirements": plan.requirements,
        "participants": [
            {
                "user_id": str(row.user.id),
                "membership_period": row.membership_period,
                "requirements": row.requirements,
                "owner_disclosures": row.owner_disclosures,
            }
            for row in plan.participants.exclude(status="withdrawn")
            .select_related("user")
            .order_by("user__id")
        ],
    }


def freeze(plan):
    value = snapshot(plan)
    return AcademicRequirementRevision.objects.create(
        plan=plan,
        revision=plan.requirements_revision,
        snapshot=value,
        digest=fingerprint(value),
    )


def current_digest(plan):
    return fingerprint(snapshot(plan))


def save_plan(user, data, plan=None):
    if plan:
        check_revision(plan.revision, data["expected_revision"])
        if plan.status != "planning" or not coordinator_for(user, plan):
            raise PermissionDenied("This plan cannot be edited by this account.")
        if str(data.get("group_id") or "") != str(
            plan.group.id if plan.group_id else ""
        ):
            raise ValidationError(
                {"group_id": "A plan cannot change its canonical group."}
            )
    else:
        check_revision(0, data["expected_revision"])
    group = None
    if data.get("group_id"):
        group = get_object_or_404(
            HousingGroup.objects.select_for_update(),
            id=data["group_id"],
            status="active",
        )
        if not group.memberships.filter(
            user=user, status="active", role="admin"
        ).exists():
            raise PermissionDenied("Select a group you currently coordinate.")
    ids = set(map(str, data["participant_ids"]))
    memberships = (
        {
            str(m.user.id): m
            for m in group.memberships.filter(status="active").select_related("user")
        }
        if group
        else {}
    )
    if (group and not ids <= memberships.keys()) or (
        not group and ids != {str(user.id)}
    ):
        raise ValidationError(
            {
                "participant_ids": "Select only intended occupants from the canonical active group."
            }
        )
    if data["starts_on"] < timezone.localdate() and (
        plan is None or data["starts_on"] != plan.starts_on
    ):
        raise ValidationError(
            {"starts_on": "Confirm a current or future accommodation date."}
        )
    raw = dict(
        data["criteria"],
        start_on=str(data["starts_on"]),
        end_on=str(data["ends_on_exclusive"]),
        people=len(ids),
    )
    validated = criteria(
        raw, allow_existing_start=bool(plan and data["starts_on"] == plan.starts_on)
    )
    if (
        validated["price_period"] != "monthly"
        or not validated.get("budget_min")
        or not validated.get("budget_max")
    ):
        raise ValidationError(
            {
                "criteria": "Supply both monthly EGP affordability bounds. Academic periods are dates, not invoice periods."
            }
        )
    requirements = validate_destinations(data["requirements"])
    previous = (
        plan_for(user, data["previous_plan_id"])
        if data.get("previous_plan_id")
        else None
    )
    if previous and previous.group_id != (group.pk if group else None):
        raise ValidationError(
            {"previous_plan_id": "Use the same individual or group context."}
        )
    lease = (
        get_object_or_404(Lease, id=data["current_lease_id"], tenant=user)
        if data.get("current_lease_id")
        else None
    )
    if plan is None:
        plan = AcademicHousingPlan(owner=user, group=group)
    else:
        plan.revision += 1
        plan.requirements_revision += 1
    for key in (
        "label",
        "period_kind",
        "starts_on",
        "ends_on_exclusive",
        "budget_basis",
    ):
        setattr(plan, key, data[key])
    plan.criteria, plan.requirements = validated, requirements
    plan.previous_plan, plan.current_lease = previous, lease
    plan.roster_revision = group.roster_revision if group else 0
    plan.access_group_revision = group.revision if group else 0
    plan.save()
    plan.participants.exclude(user__id__in=ids).update(
        status="withdrawn", reviewed_revision=0, reviewed_digest=""
    )
    for identifier in sorted(ids):
        member = memberships.get(identifier)
        actor = member.user if member else user
        row, _ = AcademicPlanParticipant.objects.get_or_create(plan=plan, user=actor)
        # Rejoining never revives a previous membership period's consent.
        row.membership, row.membership_period = member, (
            member.joined_revision if member else 0
        )
        row.status, row.reviewed_revision, row.reviewed_digest = "invited", 0, ""
        row.save()
    freeze(plan)
    audit(plan, user, "academic_plan.saved")
    return plan


def save_requirements(user, plan, data):
    check_revision(plan.revision, data["expected_revision"])
    row = get_object_or_404(plan.participants.select_related("membership"), user=user)
    if (
        plan.status != "planning"
        or row.status == "withdrawn"
        or not participant_current(row)
    ):
        raise PermissionDenied("Current participation is required.")
    low, high = money_minor(data["budget_min"]), money_minor(data["budget_max"])
    if low > high:
        raise ValidationError({"budget_max": "Maximum must be at least the minimum."})
    row.requirements = {
        **validate_destinations(data["requirements"]),
        "budget_min": money(low),
        "budget_max": money(high),
    }
    row.owner_disclosures = sorted(set(data["owner_disclosures"]))
    row.status, row.reviewed_revision, row.reviewed_digest = "pending_review", 0, ""
    row.save()
    plan.revision += 1
    plan.requirements_revision += 1
    plan.save(update_fields=["revision", "requirements_revision", "updated_at"])
    freeze(plan)
    audit(plan, user, "academic_requirements.saved")
    return plan


def blockers(plan):
    result = []
    if plan.status != "planning":
        result.append("plan_completed")
    if plan.group_id and plan.roster_revision != plan.group.roster_revision:
        result.append("roster_changed")
    rows = list(
        plan.participants.exclude(status="withdrawn").select_related("membership")
    )
    if not rows:
        result.append("incomplete_group")
    for row in rows:
        if not participant_current(row):
            result.append("membership_revoked")
        if not row.requirements:
            result.append("missing_requirements")
        if (
            row.reviewed_revision != plan.requirements_revision
            or row.reviewed_digest != current_digest(plan)
        ):
            result.append("waiting_for_consent")
    return list(dict.fromkeys(result))


def review(user, plan, data, *, withdraw=False):
    check_revision(plan.revision, data["expected_revision"])
    row = get_object_or_404(plan.participants.select_related("membership"), user=user)
    digest = current_digest(plan)
    if data["digest"] != digest:
        raise RentalConflict(
            "Review the current requirements.", code="document_changed"
        )
    if plan.status != "planning" or not participant_current(row):
        raise PermissionDenied("Current participation is required.")
    if plan.group_id and plan.roster_revision != plan.group.roster_revision:
        raise RentalConflict("Review the changed group roster.", code="roster_changed")
    if not withdraw and (
        data["consent"] is not True or not row.requirements or row.status == "withdrawn"
    ):
        raise ValidationError(
            {
                "consent": "Review your requirements and explicitly confirm participation."
            }
        )
    decision = "withdraw" if withdraw else "accept"
    RentalConsentRecord.objects.get_or_create(
        actor=user,
        subject_kind="academic_plan",
        subject_id=plan.id,
        subject_revision=plan.requirements_revision,
        decision=decision,
        defaults={
            "terms_digest": digest,
            "policy_version": "student-planning-v1",
            "snapshot": snapshot(plan),
        },
    )
    row.status = "withdrawn" if withdraw else "accepted"
    row.reviewed_revision, row.reviewed_digest = (
        (0, "") if withdraw else (plan.requirements_revision, digest)
    )
    row.save()
    plan.revision += 1
    if withdraw:
        plan.requirements_revision += 1
    plan.save(update_fields=["revision", "requirements_revision", "updated_at"])
    if withdraw:
        freeze(plan)
    audit(plan, user, "academic_plan." + decision)
    return plan


def payload(plan, user):
    value = snapshot(plan)
    # Other participants see only the explicitly shared requirement categories.
    from .publication import disclosed_requirements
    from .profiles import requirements_payload

    value["requirements"] = requirements_payload(plan.requirements)
    rows = list(plan.participants.select_related("user", "membership"))
    value["participants"] = [
        {
            "user_id": str(row.user.id),
            "name": row.user.get_full_name or "",
            "is_current_user": row.user_id == user.pk,
            "status": row.status,
            "current_membership": participant_current(row),
            "requirements": requirements_payload(
                row.requirements
                if row.user_id == user.pk
                else disclosed_requirements(row)
            ),
            "owner_disclosures": row.owner_disclosures,
            "reviewed_revision": row.reviewed_revision,
            "lease_id": (
                str(row.lease.id) if row.lease_id and row.user_id == user.pk else None
            ),
        }
        for row in rows
    ]
    value["criteria"] = criteria_payload(plan.criteria)
    shared = [disclosed_requirements(row) for row in rows if row.status != "withdrawn"]
    value["discussion_points"] = []
    if (
        len(
            {
                tuple(sorted(r.get("campus_ids", [])))
                for r in shared
                if r.get("campus_ids")
            }
        )
        > 1
    ):
        value["discussion_points"].append("different_campuses")
    if plan.budget_basis == "per_person" and any(
        (r.get("budget_max") or {}).get("amount_minor", 10**15)
        < plan.criteria["budget_max"]["amount_minor"]
        for r in shared
    ):
        value["discussion_points"].append("affordability_difference")
    value.update(
        revision=plan.revision,
        requirements_revision=plan.requirements_revision,
        status=plan.status,
        digest=current_digest(plan),
        blocking_reasons=blockers(plan),
        allowed_actions=(
            ["edit", "publish", "complete"]
            if coordinator_for(user, plan) and plan.status == "planning"
            else []
        )
        + (
            ["requirements", "review", "withdraw"]
            if any(r.user_id == user.pk and r.status != "withdrawn" for r in rows)
            and plan.status == "planning"
            else []
        ),
        requests=[
            {"id": str(r.id), "plan_revision": r.academic_revision, "status": r.status}
            for r in plan.housing_requests.order_by("-created_at")
        ],
        application_ids=[str(p.id) for p in plan.groupprocess_set.all()],
        current_lease_id=(
            str(plan.current_lease.id)
            if plan.current_lease_id and plan.current_lease.tenant_id == user.pk
            else None
        ),
        previous_plan_id=str(plan.previous_plan.id) if plan.previous_plan_id else None,
    )
    from ...models import RentalOperationalCase

    value["case_ids"] = [
        str(item.id)
        for item in RentalOperationalCase.objects.filter(
            opened_by=user, baseline__academic_plan_id=str(plan.id)
        )
    ]
    return value
