"""Bounded current choices, never authority from an editable client role flag."""

from core_apps.users.models import User
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from ..rental_lifecycle.common import staff_role
from . import tenancy_commercial as commercial, tenancy_access as access


def choices(item, user, roles):
    approvers = []
    if roles & {"owner", "signer"}:
        for row in item.lease.renter_company.memberships.filter(
            is_active=True, is_approver=True
        ).select_related("user")[:100]:
            try:
                commercial.approver(item, row.id, user)
            except PermissionDenied:
                continue
            approvers.append({"id": str(row.id), "name": row.user.get_full_name})
    candidates = []
    props = access.properties(item)
    if (
        roles & {"owner", "signer"}
        and props
        and len({p.owner_id for p in props}) == 1
        and all(p.is_ownership_verified for p in props)
        and props[0].owner_id != item.lease.owner_id
    ):
        person = props[0].owner
        candidates = [{"id": str(person.id), "name": person.get_full_name}]
    operators = []
    if roles & {"owner", "payer"}:
        from django.db.models import Q

        for actor in User.objects.filter(is_active=True, is_verified=True).filter(
            Q(is_superuser=True)
            | Q(
                staff_profile__is_active=True,
                staff_profile__role_name="financial_approver",
            )
        )[:100]:
            if actor.pk not in {
                item.lease.owner_id,
                item.coordinator_id,
                item.signer_mandate.membership.user_id,
                item.payer_mandate.membership.user_id,
            } and not access.member(item, actor):
                operators.append({"id": str(actor.id), "name": actor.get_full_name})
    return {
        "commercial_approvers": approvers,
        "ownership_candidates": candidates,
        "financial_reviewers": operators,
        "amendment_dates": (
            [
                str(p.start)
                for p in item.lease.billing_periods.filter(
                    status="scheduled", start__gte=timezone.localdate()
                )
                if not hasattr(p, "invoice")
            ]
            if roles & {"owner", "signer"}
            else []
        ),
    }
