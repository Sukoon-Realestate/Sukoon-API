"""Current corporate authority, exact portfolio locks and private projections."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied
from core_apps.common.recovery import require_scope
from core_apps.properties.models import Property
from core_apps.users.models import User
from ...models import Company, CompanyMembership, CompanyTenancy, Lease
from ..rental_phase2 import RentalConflict
from ..rental_lifecycle.common import require_actor
from . import mandates


def execution_mandate(mandate, *, exposure=0):
    return bool(
        mandates.current(mandate, exposure=exposure)
        and mandate.execution_reviewed_by_id
        and mandate.execution_reference
        and mandate.execution_verified_until
        and mandate.execution_verified_until > timezone.now()
        and mandate.execution_reviewed_by_id
        not in {
            mandate.proposed_by_id,
            mandate.reviewed_by_id,
            mandate.membership.user_id,
        }
    )


def properties(item, *, lock=False):
    ids = [unit["id"] for unit in item.source_snapshot["inventory"]["units"]]
    query = Property.objects.filter(id__in=ids).order_by("pkid")
    return list(query.select_for_update() if lock else query)


def lock_lease(lease):
    """Lock the same company root as membership changes, then every physical unit."""
    Company.objects.select_for_update().get(pk=lease.renter_company_id)
    item = CompanyTenancy.objects.get(lease=lease)
    properties(item, lock=True)
    return Lease.objects.select_for_update().get(pk=lease.pk)


def member(item, user):
    return CompanyMembership.objects.filter(
        company_id=item.lease.renter_company_id, user=user, is_active=True
    ).first()


PRIVATE_ONLY = {
    "employee",
    "incoming_employee",
    "approver",
    "new_owner",
    "financial_reviewer",
}
OPEN_REVIEW = [
    "pending",
    "waiting_departure",
    "accepted",
    "pending_signatures",
    "review_required",
]


def roles(item, user):
    if not user or not user.is_active:
        return set()
    from ...models import PrivateAccessRevocation

    if PrivateAccessRevocation.objects.filter(lease=item.lease, user=user).exists():
        return set()
    result = {"owner"} if user.pk == item.lease.owner_id else set()
    membership = member(item, user)
    if membership:
        if membership.is_admin:
            result.add("administrator")
        if membership.is_coordinator and item.coordinator_id == user.pk:
            result.add("coordinator")
        if item.signer_mandate.membership_id == membership.pk:
            result.add("signer")
        if item.payer_mandate.membership_id == membership.pk:
            result.add("payer")
    if item.preparation.booking.assignments.filter(employee=user).exists():
        result.add("employee")
    for change in item.changes.filter(state__in=OPEN_REVIEW):
        for role, identity in change.snapshot["required"].items():
            if (
                identity == str(user.id)
                and role
                in {
                    "incoming_employee",
                    "new_signer",
                    "new_payer",
                    "new_coordinator",
                    "approver",
                    "new_owner",
                    "financial_reviewer",
                }
                and (membership or role in {"new_owner", "financial_reviewer"})
            ):
                if role == "approver" and not membership.is_approver:
                    continue
                if role == "financial_reviewer":
                    from ..rental_lifecycle.common import staff_role

                    if not staff_role(user, {"financial_approver"}):
                        continue
                if role == "new_owner" and any(
                    p.owner_id != user.pk or not p.is_ownership_verified
                    for p in properties(item)
                ):
                    continue
                result.add(role)
    return result


def get(user, identity, *, lock=False):
    require_scope("company_authority")
    require_actor(user)
    item = get_object_or_404(
        CompanyTenancy.objects.select_related("lease"), id=identity
    )
    if not roles(item, user):
        raise NotFound()
    if lock:
        lease = lock_lease(item.lease)
        item = CompanyTenancy.objects.select_for_update(of=("self",)).get(pk=item.pk)
        item.lease = lease
        if not roles(item, User.objects.get(pk=user.pk)):
            raise NotFound()
    return item


def visible(user):
    ordinary = CompanyTenancy.objects.filter(
        Q(lease__owner=user)
        | Q(preparation__booking__assignments__employee=user)
        | (
            Q(
                lease__renter_company__memberships__user=user,
                lease__renter_company__memberships__is_active=True,
            )
            & (
                Q(lease__renter_company__memberships__is_admin=True)
                | Q(
                    coordinator=user,
                    lease__renter_company__memberships__is_coordinator=True,
                )
                | Q(signer_mandate__membership__user=user)
                | Q(payer_mandate__membership__user=user)
            )
        )
    )
    invited = CompanyTenancy.objects.filter(
        lease__renter_company__memberships__user=user,
        lease__renter_company__memberships__is_active=True,
        changes__state__in=OPEN_REVIEW,
    ).filter(
        Q(changes__snapshot__required__incoming_employee=str(user.id))
        | Q(changes__snapshot__required__new_signer=str(user.id))
        | Q(changes__snapshot__required__new_payer=str(user.id))
        | Q(changes__snapshot__required__new_coordinator=str(user.id))
        | Q(changes__snapshot__required__approver=str(user.id))
    )
    external = CompanyTenancy.objects.filter(changes__state__in=OPEN_REVIEW).filter(
        Q(changes__snapshot__required__new_owner=str(user.id))
        | Q(changes__snapshot__required__financial_reviewer=str(user.id))
    )
    return (
        (ordinary | invited | external)
        .exclude(lease__private_access_revocations__user=user)
        .distinct()
        .order_by("-created_at", "id")
    )


def require_role(item, user, allowed, *, sensitive=False):
    current = User.objects.get(pk=user.pk)
    require_actor(current)
    if not roles(item, current) & set(allowed):
        raise PermissionDenied(
            "This action requires the assigned company responsibility."
        )
    if sensitive and current.sensitive_actions_frozen:
        raise PermissionDenied(
            "Recover account authority before creating a new commitment."
        )
    return current


def require_delegate(item, user, kind):
    require_role(item, user, {"signer" if kind == "sign" else "payer"}, sensitive=True)
    mandate = item.signer_mandate if kind == "sign" else item.payer_mandate
    from .tenancy_commercial import exposure

    if not execution_mandate(mandate, exposure=exposure(item)):
        raise RentalConflict(
            "An independently verified current company mandate is required.",
            code="execution_authority_required",
        )


def commercial_read(lease, user):
    if not lease.renter_company_id:
        return user.pk in {lease.owner_id, lease.tenant_id}
    require_scope("company_authority")
    return bool(roles(lease.company_tenancy, user) - PRIVATE_ONLY)


def can_pay(lease, user):
    if not lease.renter_company_id:
        return user.pk == lease.tenant_id
    try:
        require_scope("company_authority")
        require_delegate(lease.company_tenancy, user, "pay")
        return True
    except (PermissionDenied, RentalConflict):
        return False


def notify(item):
    from ...planning_models import PlanningEvent

    booking = item.preparation.booking
    people = {
        item.lease.owner_id,
        item.coordinator_id,
        item.signer_mandate.membership.user_id,
        item.payer_mandate.membership.user_id,
    }
    people.update(booking.assignments.values_list("employee_id", flat=True))
    people.update(
        item.lease.renter_company.memberships.filter(
            is_active=True, is_admin=True
        ).values_list("user_id", flat=True)
    )
    for change in item.changes.filter(state__in=OPEN_REVIEW):
        people.update(
            User.objects.filter(
                id__in=change.snapshot["required"].values()
            ).values_list("pk", flat=True)
        )
    for identity in people:
        PlanningEvent.objects.get_or_create(
            recipient_id=identity,
            event_key=f"company.tenancy:{item.id}:{item.revision}",
            defaults={
                "destination": {
                    "action_type": "open_company_tenancy",
                    "target_id": str(item.id),
                    "schema_version": "1",
                    "workspace": (
                        "owner" if identity == item.lease.owner_id else "tenant"
                    ),
                }
            },
        )


def changed(item, actor, action, reason="", metadata=None):
    from ..rental_lifecycle.common import audit

    item.lease.revision += 1
    item.lease.save()
    audit(item.lease, actor, action, reason, metadata or {})
    notify(item)
    return item
