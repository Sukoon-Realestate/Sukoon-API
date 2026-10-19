"""Participant access for ordinary corporate contract preparation."""

from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from ...company_models import Company, CompanyMembership
from ...company_contract_models import CompanyContractPreparation
from ..rental_lifecycle.common import require_actor


def roles_for(item, user):
    snapshot = item.snapshot
    roles = []
    member = CompanyMembership.objects.filter(
        company=item.booking.request.company, user=user, is_active=True
    ).first()
    if user.pk == item.booking.offer.owner_id and str(user.id) == snapshot["owner_id"]:
        from core_apps.properties.models import Property

        ids = [p["id"] for p in snapshot["inventory"]["units"]]
        if ids and Property.objects.filter(id__in=ids, owner=user).count() == len(ids):
            roles.append("owner")
    if member:
        if str(user.id) == snapshot["signer_id"]:
            roles.append("signer")
        if str(user.id) == snapshot["payer_id"]:
            roles.append("payer")
        if member.is_employee and any(
            r["employee_id"] == str(user.id) for r in snapshot["placements"]
        ):
            staff = getattr(member, "staff_record", None)
            if staff is None or staff.employment_status == "active":
                roles.append("employee")
    return roles


def manages(item, user):
    return bool(
        item.booking.request.coordinator_id == user.pk
        and CompanyMembership.objects.filter(
            company=item.booking.request.company,
            user=user,
            is_active=True,
            is_coordinator=True,
        ).exists()
    )


def can_read(item, user):
    # The original counterparty retains its historical review. A new property
    # owner does not inherit private employee reviews or the old owner's consent.
    return bool(
        user
        and user.is_active
        and user.is_verified
        and (
            str(user.id) == item.snapshot["owner_id"]
            or roles_for(item, user)
            or manages(item, user)
            or CompanyMembership.objects.filter(
                company=item.booking.request.company,
                user=user,
                is_active=True,
                is_admin=True,
            ).exists()
        )
    )


def get(user, identity, *, lock=False):

    require_actor(user)
    item = get_object_or_404(CompanyContractPreparation, id=identity)
    if lock:
        Company.objects.select_for_update().get(pk=item.booking.request.company_id)
        item = CompanyContractPreparation.objects.select_for_update().get(pk=item.pk)
    if not can_read(item, user):
        raise NotFound()
    return item


def visible(user):

    require_actor(user)
    membership = Q(
        booking__request__company__memberships__user=user,
        booking__request__company__memberships__is_active=True,
    )
    return (
        CompanyContractPreparation.objects.filter(
            Q(snapshot__owner_id=str(user.id))
            | membership
            & (
                Q(booking__request__company__memberships__is_admin=True)
                | Q(
                    booking__request__coordinator=user,
                    booking__request__company__memberships__is_coordinator=True,
                )
                | Q(
                    consents__actor=user, consents__snapshot_digest=F("snapshot_digest")
                )
                & (
                    Q(consents__role__in=["signer", "payer"])
                    | Q(
                        consents__role="employee",
                        booking__request__company__memberships__is_employee=True,
                    )
                    & (
                        Q(
                            booking__request__company__memberships__staff_record__isnull=True
                        )
                        | Q(
                            booking__request__company__memberships__staff_record__employment_status="active"
                        )
                    )
                )
            )
        )
        .distinct()
        .order_by("-updated_at", "id")
    )
