"""Explicit company preparation authority, independent of financial assurance."""

from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from ...company_models import CompanyMembership
from ...company_contract_models import CompanyMandate
from ..rental_lifecycle.common import audit, require_revision, require_actor
from ..rental_phase2 import RentalConflict
from .access import company_for, member_for


def notify(item):
    from ...planning_models import PlanningEvent

    users = list(
        item.company.memberships.filter(
            is_active=True, is_admin=True, user__is_active=True
        ).values_list("user_id", flat=True)
    )
    users.append(item.membership.user_id)
    for identity in set(users):
        PlanningEvent.objects.get_or_create(
            recipient_id=identity,
            event_key=f"company.mandate:{item.id}:{item.revision}",
            defaults={
                "destination": {
                    "action_type": "open_company_mandates",
                    "target_id": str(item.company.id),
                    "mandate_id": str(item.id),
                    "schema_version": "1",
                    "workspace": "tenant",
                }
            },
        )


def current(mandate, *, kind=None, exposure=0):
    member = mandate.membership
    return bool(
        mandate.state == "approved"
        and mandate.currency == "EGP"
        and (kind is None or mandate.kind == kind)
        and mandate.valid_from <= timezone.now() < mandate.valid_until
        and mandate.limit_minor >= exposure
        and mandate.membership_revision == member.revision
        and member.company_id == mandate.company_id
        and member.is_active
        and member.user.is_active
        and member.user.is_verified
        and not member.user.sensitive_actions_frozen
        and mandate.reviewed_by_id
        and mandate.reviewed_by_id not in {mandate.proposed_by_id, member.user_id}
    )


def authorize(user, identity, *, lock=False, admin=False):
    initial = get_object_or_404(CompanyMandate, id=identity)
    company = company_for(
        user, initial.company.id, "admin" if admin else "read", lock=lock
    )
    query = (
        CompanyMandate.objects.select_for_update(of=("self",))
        if lock
        else CompanyMandate.objects
    )
    result = get_object_or_404(
        query.select_related("membership__user", "company"), pk=initial.pk
    )
    member = member_for(user, company)
    if not (
        member.is_admin or member.is_coordinator or result.membership.user_id == user.pk
    ):
        raise PermissionDenied("This mandate is outside your company responsibilities.")
    return result


@transaction.atomic
def propose(user, company_id, data):
    company = company_for(user, company_id, "admin", lock=True)
    if type(user).objects.get(pk=user.pk).sensitive_actions_frozen:
        raise PermissionDenied(
            "Restore active account authority before approving this company plan."
        )
    require_revision(company, data["expected_revision"])
    if (
        company.review_status != "verified"
        or not company.reviewed_by_id
        or not company.review_reference
    ):
        raise RentalConflict(
            "Complete the company authority review before proposing a mandate.",
            code="company_review_required",
        )
    member = get_object_or_404(
        CompanyMembership,
        company=company,
        id=data["membership_id"],
        is_active=True,
        user__is_active=True,
        user__is_verified=True,
    )
    now = timezone.now()
    if data["valid_until"] <= max(now, data["valid_from"]) or data[
        "valid_until"
    ] - data["valid_from"] > timedelta(days=366):
        raise ValidationError(
            "Choose a future mandate expiry within 366 days of its start."
        )
    if CompanyMandate.objects.filter(
        company=company,
        membership=member,
        kind=data["kind"],
        state__in=["pending", "approved"],
        valid_until__gt=now,
    ).exists():
        raise RentalConflict(
            "Resolve or revoke the existing mandate before replacing it.",
            code="mandate_exists",
        )
    item = CompanyMandate.objects.create(
        company=company,
        membership=member,
        membership_revision=member.revision,
        proposed_by=user,
        **{
            k: data[k]
            for k in (
                "kind",
                "valid_from",
                "valid_until",
                "limit_minor",
                "evidence_reference",
                "reason",
            )
        },
    )
    audit(item, user, "company_mandate_proposed", data["reason"])
    notify(item)
    return item


@transaction.atomic
def decide(user, identity, action, data):
    item = authorize(user, identity, lock=True, admin=action != "revoke")
    member = member_for(user, item.company)
    require_revision(item, data["expected_revision"])
    if action == "revoke":
        if not member.is_admin and item.membership.user_id != user.pk:
            raise PermissionDenied(
                "Only an administrator or the delegate can revoke this mandate."
            )
        if item.state not in {"pending", "approved"}:
            raise RentalConflict(
                "This mandate is already closed.", code="mandate_closed"
            )
        item.state = "revoked"
    else:
        if type(user).objects.get(pk=user.pk).sensitive_actions_frozen:
            raise PermissionDenied(
                "Restore active account authority before approving this company plan."
            )
        if user.pk in {item.proposed_by_id, item.membership.user_id}:
            raise PermissionDenied(
                "An independent administrator must review this mandate."
            )
        if (
            item.state != "pending"
            or item.valid_until <= timezone.now()
            or item.membership_revision != item.membership.revision
            or not item.membership.is_active
        ):
            raise RentalConflict(
                "Refresh the mandate and current membership before review.",
                code="mandate_changed",
            )
        require_actor(item.membership.user)
        item.state = "approved" if action == "approve" else "rejected"
        item.reviewed_by, item.reviewed_at = user, timezone.now()
    item.revision += 1
    item.save()
    audit(item, user, "company_mandate_" + action, data["reason"])
    notify(item)
    return item


def payload(item, user):
    from .tenancy_access import execution_mandate

    member = member_for(user, item.company)
    independent = member.is_admin and user.pk not in {
        item.proposed_by_id,
        item.membership.user_id,
    }
    valid_pending = (
        item.state == "pending"
        and item.valid_until > timezone.now()
        and item.membership_revision == item.membership.revision
        and item.membership.is_active
        and item.membership.user.is_active
        and item.membership.user.is_verified
    )
    actions = (
        ["approve", "reject"]
        if independent and valid_pending and not user.sensitive_actions_frozen
        else []
    )
    if item.state in {"pending", "approved"} and (
        member.is_admin or item.membership.user_id == user.pk
    ):
        actions += ["revoke"]
    return {
        "id": str(item.id),
        "company_id": str(item.company.id),
        "revision": item.revision,
        "membership_id": str(item.membership.id),
        "delegate_id": str(item.membership.user.id),
        "delegate_name": item.membership.user.get_full_name,
        "kind": item.kind,
        "state": item.state,
        "effective": current(item),
        "actions": actions,
        "valid_from": item.valid_from.isoformat(),
        "valid_until": item.valid_until.isoformat(),
        "limit_minor": item.limit_minor,
        "currency": item.currency,
        "exponent": 2,
        "evidence_reference": item.evidence_reference if member.is_admin else "",
        "reason": (
            item.reason if member.is_admin or item.membership.user_id == user.pk else ""
        ),
        "binding_execution_authorized": execution_mandate(item),
        "execution_verified_until": (
            item.execution_verified_until.isoformat()
            if item.execution_verified_until
            else None
        ),
    }
