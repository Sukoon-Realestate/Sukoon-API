import uuid

from django.core.exceptions import ValidationError as DjangoValidationError

from django.utils import timezone
from rest_framework.exceptions import NotFound

from ..models import Lease
from ..planning_models import (
    CommuteSearch,
    ConditionReport,
    GroupInvitation,
    HousingGroup,
    HousingOffer,
    HousingRequest,
    LifestyleProfile,
    RoommateConnection,
    TenancyTransition,
    TenantAssistantTurn,
)
from .planning import eligible_owner


def planning_subject(user, identifier):
    """Resolve a private planning result for operation recovery and capability reads."""
    try:
        identifier = uuid.UUID(str(identifier))
    except (ValueError, TypeError):
        raise NotFound()
    for model in (LifestyleProfile, CommuteSearch, TenantAssistantTurn):
        item = model.objects.filter(id=identifier, user=user).first()
        if item:
            if hasattr(item, "expires_at") and item.expires_at <= timezone.now():
                raise NotFound()
            return item
    from ..planning_roommate_views import connections

    item = connections(user).filter(id=identifier).first()
    if item:
        return item
    group = HousingGroup.objects.filter(
        id=identifier, memberships__user=user, memberships__status="active"
    ).first()
    if group:
        return group
    invite = GroupInvitation.objects.filter(
        id=identifier,
        group__memberships__user=user,
        group__memberships__role="admin",
        group__memberships__status="active",
    ).first()
    if invite:
        return invite
    from ..planning_housing_views import can_read_request, get_offer

    item = HousingRequest.objects.filter(id=identifier).first()
    if item and can_read_request(user, item):
        return item
    if HousingOffer.objects.filter(id=identifier).exists():
        return get_offer(user, identifier)
    from ..planning_condition_views import participant_lease

    for model in (ConditionReport, TenancyTransition):
        item = model.objects.filter(id=identifier).first()
        if item:
            if (
                isinstance(item, TenancyTransition)
                and item.candidate_id
                and item.candidate.tenant_id == user.pk
            ):
                return item
            participant_lease(user, item.lease.id)
            return item
    raise NotFound()


def planning_actions(user, capability, subject_id=""):
    general = {
        "lifestyle": ["read", "save"],
        "roommates": ["read", "request", "block"],
        "housing_groups": ["read", "create", "preview_invite", "join"],
        "housing_requests": ["read", "publish"],
        "housing_offers": ["read"] + (["offer"] if eligible_owner(user) else []),
        "condition_reports": ["read", "submit"],
        "move_out_notices": ["read", "submit"],
        "replacements": ["read", "submit"],
        "commute": ["read", "search"],
        "tenant_assistant": ["ask"],
        "group_visits": ["read"],
        "group_applications": ["read"],
    }
    if not subject_id:
        actions = general.get(capability, [])
        if (
            capability == "housing_groups"
            and HousingGroup.objects.filter(
                status="active",
                memberships__user=user,
                memberships__role="admin",
                memberships__status="active",
            ).exists()
        ):
            actions += ["create_invite"]
        return actions
    try:
        if (
            capability in {"condition_reports", "move_out_notices", "replacements"}
            and Lease.objects.filter(id=subject_id).exists()
        ):
            from ..planning_condition_views import participant_lease

            lease = participant_lease(user, subject_id)
            return ["read"] + (
                ["create", "submit"]
                if not lease.legacy_read_only
                and lease.status in {"active", "termination_pending", "ended"}
                else []
            )
        item = planning_subject(user, subject_id)
    except (NotFound, ValueError, DjangoValidationError):
        # A private join link is validated by the join endpoint; this grants only
        # permission to present a token, never permission to read a group.
        return ["join"] if capability == "housing_groups" else []
    if capability == "lifestyle" and isinstance(item, LifestyleProfile):
        return ["read", "save"]
    if capability == "roommates" and isinstance(item, RoommateConnection):
        from ..planning_roommate_views import roommate_actions

        return ["read", *roommate_actions(user, item)]
    if isinstance(item, HousingGroup) and capability in {
        "housing_groups",
        "group_visits",
        "group_applications",
    }:
        from ..planning_group_views import group_actions

        actions = group_actions(user, item)
        if capability == "group_visits":
            actions = [x for x in actions if "visit" in x]
        elif capability == "group_applications":
            actions = [x for x in actions if "application" in x or x == "apply"]
        return ["read", *actions]
    if isinstance(item, GroupInvitation) and capability == "housing_groups":
        return ["read_invite"]
    if isinstance(item, HousingRequest) and capability == "housing_requests":
        from ..planning_housing_views import request_actions

        return ["read", *request_actions(user, item)]
    if isinstance(item, HousingOffer) and capability == "housing_offers":
        from ..planning_housing_views import offer_actions

        return ["read", *offer_actions(user, item)]
    if isinstance(item, ConditionReport) and capability == "condition_reports":
        from ..planning_condition_views import report_actions

        return ["read", *report_actions(user, item)]
    if isinstance(item, TenancyTransition) and capability == (
        "move_out_notices" if item.kind == "moveOutNotice" else "replacements"
    ):
        if item.candidate_id and item.candidate.tenant_id == user.pk:
            return (
                ["accept_candidate_nomination", "decline_candidate_nomination"]
                if item.status == "candidate_pending"
                else []
            )
        from ..planning_transition_views import transition_actions

        return ["read", *transition_actions(user, item)]
    if isinstance(item, CommuteSearch) and capability == "commute":
        return ["read"]
    return []
