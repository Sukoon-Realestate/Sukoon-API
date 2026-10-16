import hashlib
import secrets
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied
from ...company_models import Company, CompanyMembership, CompanyInvitation
from ..rental_lifecycle.common import audit, require_revision, require_actor
from ..rental_phase2 import RentalConflict
from .access import company_for, require_new_business

ROLES = {"admin", "coordinator", "approver", "employee"}


def create_company(user, data):
    require_new_business()
    company = Company.objects.create(
        **{key: data[key] for key in ("name", "registration_number", "contact_email")}
    )
    CompanyMembership.objects.create(company=company, user=user, is_admin=True)
    audit(company, user, "company_created")
    return company


@transaction.atomic
def invite(user, company_id, email, roles):
    company = company_for(user, company_id, "admin", lock=True)
    if not roles or set(roles) - ROLES:
        raise ValidationError({"roles": "Select supported company roles."})
    token = secrets.token_urlsafe(32)
    invitation = CompanyInvitation.objects.create(
        company=company,
        invited_by=user,
        recipient_email=email.strip().lower(),
        token_digest=hashlib.sha256(token.encode()).hexdigest(),
        roles=sorted(set(roles)),
        expires_at=timezone.now() + timedelta(days=7),
    )
    audit(
        invitation,
        user,
        "company_invitation_created",
        metadata={"company_id": str(company.id)},
    )
    # No email is sent here. The caller may explicitly share the one-time token.
    return invitation, token


@transaction.atomic
def accept_invitation(user, token):
    require_actor(user)
    digest = hashlib.sha256(token.encode()).hexdigest()
    invitation = CompanyInvitation.objects.filter(token_digest=digest).first()
    if invitation is None:
        raise PermissionDenied("The invitation is invalid or unavailable.")
    Company.objects.select_for_update().get(pk=invitation.company_id)
    invitation = CompanyInvitation.objects.select_for_update().get(pk=invitation.pk)
    if not CompanyMembership.objects.filter(
        company_id=invitation.company_id,
        user_id=invitation.invited_by_id,
        is_active=True,
        is_admin=True,
        user__is_active=True,
        user__is_verified=True,
    ).exists():
        raise PermissionDenied("The invitation is invalid or unavailable.")
    if invitation.recipient_email.casefold() != user.email.casefold():
        raise PermissionDenied("The invitation belongs to another recipient.")
    if (
        invitation.consumed_at
        or invitation.revoked_at
        or invitation.expires_at <= timezone.now()
    ):
        raise RentalConflict(
            "The invitation is no longer available.", code="invitation_expired"
        )
    member, created = CompanyMembership.objects.get_or_create(
        company=invitation.company, user=user
    )
    if not created and member.is_active:
        raise RentalConflict(
            "The recipient already belongs to this company.", code="membership_exists"
        )
    # A rejoin never restores old spending or signing authority.
    member.is_active = True
    member.can_execute_payments = False
    member.signing_verified_until = None
    member.signing_reference = ""
    for role in ROLES:
        setattr(member, "is_" + role, role in invitation.roles)
    member.revision += 1
    member.save()
    invitation.consumed_at = timezone.now()
    invitation.accepted_by = user
    invitation.save()
    audit(member, user, "company_invitation_accepted")
    return member.company


@transaction.atomic
def update_member(user, company_id, membership_id, data):
    company = company_for(user, company_id, "admin", lock=True)
    from django.shortcuts import get_object_or_404

    member = get_object_or_404(
        CompanyMembership.objects.select_for_update(), company=company, id=membership_id
    )
    require_revision(member, data["expected_revision"])
    roles = set(data["roles"])
    if roles - ROLES:
        raise ValidationError({"roles": "Unsupported role."})
    active = data["is_active"]
    if member.is_admin and member.is_active and (not active or "admin" not in roles):
        if (
            not company.memberships.filter(is_active=True, is_admin=True)
            .exclude(pk=member.pk)
            .exists()
        ):
            raise RentalConflict(
                "The company must retain an active administrator.",
                code="last_administrator",
            )
    if member.is_coordinator and (not active or "coordinator" not in roles):
        if (
            company.housing_requests.filter(coordinator=member.user)
            .exclude(items__status="closed")
            .exists()
        ):
            raise RentalConflict(
                "Reassign active housing requests before removing the coordinator.",
                code="reassignment_required",
            )
    for role in ROLES:
        setattr(member, "is_" + role, role in roles)
    member.is_active = active
    # Payment is separately assigned; role changes never imply it.
    member.can_execute_payments = (
        data.get("can_execute_payments", member.can_execute_payments)
        if active
        else False
    )
    if not active:
        member.signing_verified_until = None
    member.revision += 1
    member.save()
    audit(member, user, "company_membership_changed", data.get("reason", ""))
    from core_apps.chat.services.company_access import refresh_company

    refresh_company(company, user)
    return member
