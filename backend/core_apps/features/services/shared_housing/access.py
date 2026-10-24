from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from ...shared_housing_models import SharedHousingPlan, SharedHousingAllocation
from ..planning import eligible_owner
from ..rental_phase2 import RentalConflict

CAPABILITY = "shared_housing_plans"


def members(plan):
    return [plan.connection.first, plan.connection.second]


def member_ids(plan):
    return {str(user.id) for user in members(plan)}


def is_member(plan, user):
    return user.pk in {plan.connection.first_id, plan.connection.second_id}


def visible(user):
    member = Q(connection__first=user) | Q(connection__second=user)
    own = Q(proposals__property__owner=user)
    public = (
        Q(published=True, expires_at__gt=timezone.now(), status="searching")
        if eligible_owner(user)
        else Q(pk__in=[])
    )
    return SharedHousingPlan.objects.filter(member | own | public).distinct()


def get_plan(user, identifier, *, lock=False):
    # Lock the base table, not the DISTINCT visibility join (PostgreSQL).
    permitted = visible(user).filter(id=identifier).exists()
    if not permitted:
        from rest_framework.exceptions import NotFound

        raise NotFound()
    query = SharedHousingPlan.objects.select_related(
        "connection__first", "connection__second", "coordinator"
    )
    if lock:
        from ...planning_models import RoommateConnection

        connection_id = SharedHousingPlan.objects.values_list(
            "connection_id", flat=True
        ).get(id=identifier)
        RoommateConnection.objects.select_for_update().get(pk=connection_id)
        query = query.select_for_update(of=("self",))
    return get_object_or_404(query, id=identifier)


def actions(plan, user):
    if not user.is_active or not user.is_verified:
        return []
    if plan.status in {"closed", "handed_off"}:
        return []
    member = is_member(plan, user)
    if plan.connection.status != "accepted" or plan.expires_at <= timezone.now():
        return ["withdraw"] if member else []
    if (
        not settings.SHARED_HOUSING_ENABLED
        or CAPABILITY not in settings.PLANNING_ENABLED_SERVICES
    ):
        if not member:
            return []
        privacy = ["withdraw"]
        if plan.status == "invited" and user.pk != plan.coordinator_id:
            privacy.append("decline_invite")
        if plan.published and user.pk == plan.coordinator_id:
            privacy.append("unpublish")
        return privacy
    if member:
        result = ["withdraw"]
        if plan.status == "invited":
            return result + (
                ["accept_invite", "decline_invite"]
                if user.pk != plan.coordinator_id
                else []
            )
        if plan.status == "searching":
            result += ["propose", "approve_publication", "consent_selection"]
            if user.pk == plan.coordinator_id:
                result += ["edit", "publish", "unpublish", "submit"]
        if plan.status == "reviewing":
            result += ["consent_terms", "request_changes"]
        return result
    if plan.status == "searching" and plan.published and eligible_owner(user):
        return ["propose"]
    if plan.proposals.filter(
        property__owner=user, status__in=["submitted", "terms"]
    ).exists():
        return ["owner_accept", "owner_reject", "request_changes", "send_invitations"]
    return []


def require_action(plan, user, action):
    if action not in actions(plan, user):
        raise PermissionDenied("This shared housing action is not available.")


def guard_individual(interest):
    """A paired request must not escape joint review through a legacy endpoint."""
    allocation = (
        SharedHousingAllocation.objects.filter(interest=interest)
        .select_related("proposal__plan")
        .first()
    )
    if allocation and allocation.proposal.plan.status != "handed_off":
        raise RentalConflict(
            "Review both participants in the shared housing plan.",
            code="shared_review_required",
        )


def individual_actions(interest):
    return (
        not SharedHousingAllocation.objects.filter(interest=interest)
        .exclude(proposal__plan__status="handed_off")
        .exists()
    )
