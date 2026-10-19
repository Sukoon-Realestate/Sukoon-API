from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, PermissionDenied
from ...student_models import (
    AcademicHousingPlan,
    StudentProfile,
    SharedLivingAgreement,
    StudentOfferPolicy,
)
from ...planning_models import HousingGroup
from ..planning import require_planning


def plans_for(user):
    return AcademicHousingPlan.objects.filter(
        Q(group__isnull=True, owner=user)
        | Q(
            group__status="active",
            group__memberships__user=user,
            group__memberships__status="active",
            group__memberships__joined_revision__lte=F("access_group_revision"),
        )
    ).distinct()


def plan_for(user, identifier, *, lock=False, coordinator=False):
    found = get_object_or_404(AcademicHousingPlan, id=identifier)
    if found.group_id:
        qs = HousingGroup.objects.select_for_update() if lock else HousingGroup.objects
        group = get_object_or_404(qs, pk=found.group_id, status="active")
        member = group.memberships.filter(user=user, status="active").first()
        if not member or member.joined_revision > found.access_group_revision:
            raise NotFound()
        if coordinator and member.role != "admin":
            raise PermissionDenied(
                "Only the current group coordinator can organize this plan."
            )
    elif found.owner_id != user.pk:
        raise NotFound()
    qs = (
        AcademicHousingPlan.objects.select_for_update(of=("self",))
        if lock
        else AcademicHousingPlan.objects
    )
    return qs.select_related("owner", "group").get(pk=found.pk)


def coordinator_for(user, plan):
    return (
        plan.owner_id == user.pk
        if not plan.group_id
        else plan.group.memberships.filter(
            user=user, status="active", role="admin"
        ).exists()
    )


def participant_current(row):
    return not row.plan.group_id or bool(
        row.membership
        and row.membership.group_id == row.plan.group_id
        and row.membership.user_id == row.user_id
        and row.membership.status == "active"
        and row.membership.joined_revision == row.membership_period
    )


def student_subject(user, identifier):
    from ...models import RentalSummaryGrant

    grant = RentalSummaryGrant.objects.filter(
        id=identifier, granted_by=user, lease__tenant=user
    ).first()
    if grant:
        return grant
    if AcademicHousingPlan.objects.filter(id=identifier).exists():
        return plan_for(user, identifier)
    item = StudentProfile.objects.filter(id=identifier, user=user).first()
    if item:
        return item
    item = SharedLivingAgreement.objects.filter(id=identifier).first()
    if item:
        plan_for(user, item.plan.id)
        return item
    item = StudentOfferPolicy.objects.filter(
        id=identifier, property__owner=user
    ).first()
    if item:
        return item
    return None


def actions(user, capability, subject_id=""):
    if capability == "rental_summary_sharing":
        from ...models import Lease, RentalSummaryGrant

        if not subject_id:
            return ["read"]
        if Lease.objects.filter(
            id=subject_id, tenant=user, legacy_read_only=False
        ).exists():
            return ["read", "grant"]
        if RentalSummaryGrant.objects.filter(
            id=subject_id, granted_by=user, lease__tenant=user
        ).exists():
            return ["read", "revoke"]
        return []
    if capability == "student_planning" and str(subject_id) == str(user.id):
        return ["read", "save_profile"]
    if capability == "student_planning" and not subject_id:
        return ["read", "create", "save_profile"]
    if capability == "student_verification":
        return (
            ["read", "submit_evidence"]
            if not subject_id or str(subject_id) == str(user.id)
            else []
        )
    if capability == "student_offer_policies":
        if not subject_id:
            return ["read"]
        from core_apps.properties.models import Property

        return (
            ["read", "save_policy"]
            if Property.objects.filter(id=subject_id, owner=user).exists()
            else ["read"]
        )
    if capability == "student_study_facts":
        return ["read"]
    if not subject_id:
        return ["read"]
    try:
        item = student_subject(user, subject_id)
    except NotFound:
        return []
    if isinstance(item, StudentProfile):
        return ["read", "save_profile"] if capability == "student_planning" else []
    if isinstance(item, SharedLivingAgreement):
        return (
            ["read", "approve", "discuss", "revise"]
            if capability in {"shared_living", "exam_arrangements"}
            else []
        )
    if not isinstance(item, AcademicHousingPlan):
        return []
    if capability == "student_planning":
        result = ["read"]
        if item.status == "planning":
            participant = (
                item.participants.select_related("membership").filter(user=user).first()
            )
            if (
                participant
                and participant.status != "withdrawn"
                and participant_current(participant)
            ):
                result += ["requirements", "review", "withdraw"]
            if coordinator_for(user, item):
                result += ["edit", "complete"]
        return result
    if capability == "student_demand":
        return ["read"] + (
            ["publish"]
            if coordinator_for(user, item) and item.status == "planning"
            else []
        )
    if capability in {"shared_living", "exam_arrangements"}:
        return ["read", "propose"]
    if capability == "student_transitions":
        return ["read", "link_lease", "check_in"]
    return []
