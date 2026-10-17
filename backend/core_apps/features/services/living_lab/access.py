from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from ...living_lab_models import SharedLivingLab
from ...planning_models import HousingGroup
from ..planning import enabled_services

CAPABILITY = "shared_living_lab"


def group_for(user, identifier, *, lock=False, coordinator=False):
    queryset = (
        HousingGroup.objects.select_for_update() if lock else HousingGroup.objects.all()
    )
    group = get_object_or_404(queryset, id=identifier)
    member = group.memberships.filter(user=user, status="active").first()
    if member is None:
        raise NotFound()
    if coordinator and (group.status != "active" or member.role != "admin"):
        raise PermissionDenied(
            "Only the current group coordinator can organize a living lab."
        )
    return group


def lab_for(user, identifier, *, lock=False):
    found = get_object_or_404(SharedLivingLab, id=identifier)
    group = group_for(user, found.group.id, lock=lock)
    member = group.memberships.get(user=user, status="active")
    if not any(
        row["user_id"] == str(user.id)
        and row["membership_id"] == str(member.id)
        and row["period"] == member.joined_revision
        for row in found.participant_periods
    ):
        raise NotFound()
    queryset = (
        SharedLivingLab.objects.select_for_update()
        if lock
        else SharedLivingLab.objects.all()
    )
    result = queryset.get(pk=found.pk)
    result.group = group
    return result


def roster_current(lab):
    actual = sorted(
        (str(row.user.id), str(row.id), row.joined_revision)
        for row in lab.group.memberships.filter(status="active").select_related("user")
    )
    expected = sorted(
        (row["user_id"], row["membership_id"], row["period"])
        for row in lab.participant_periods
    )
    return (
        lab.group.status == "active"
        and lab.group.roster_revision == lab.roster_revision
        and actual == expected
    )


def lab_actions(user, lab):
    result = ["withdraw"]
    if CAPABILITY not in enabled_services():
        return result
    coordinator = (
        lab.group.status == "active"
        and lab.group.memberships.filter(
            user=user, role="admin", status="active"
        ).exists()
    )
    if coordinator:
        result += ["scenario"]
    if not roster_current(lab):
        return result
    if lab.status == "closed" or lab.expires_at <= timezone.now():
        return result
    result += ["requirements", "disclose"]
    if lab.status in {"proposal_ready", "collecting_responses"}:
        result += ["respond"]
    if coordinator:
        result += ["close"]
        if lab.status != "agreed":
            result += ["run", "configure"]
        if lab.status == "agreed" and not lab.scenario.get("counterfactual"):
            if not lab.handoff_proposal_id:
                result += ["prepare_cost_proposal"]
            if (
                lab.handoff_proposal_id
                and not lab.handoff_application_id
                and "group_applications" in enabled_services()
            ):
                result += ["prepare_application"]
            if (
                not lab.handoff_tender_id
                and "collective_tender_planning" in enabled_services()
            ):
                result += ["prepare_tender"]
    return result


def subject(user, identifier):
    try:
        if SharedLivingLab.objects.filter(id=identifier).exists():
            return lab_for(user, identifier)
    except (DjangoValidationError, ValueError):
        return None
    return None


def actions(user, capability, subject_id=""):
    if capability != CAPABILITY:
        return []
    if not subject_id:
        return ["read"]
    try:
        item = subject(user, subject_id)
        if item:
            return ["read", *lab_actions(user, item)]
        group = group_for(user, subject_id)
        result = ["read"]
        if (
            CAPABILITY in enabled_services()
            and group.status == "active"
            and group.memberships.filter(
                user=user, role="admin", status="active"
            ).exists()
        ):
            result += ["create"]
        return result
    except (NotFound, DjangoValidationError, ValueError):
        return []
