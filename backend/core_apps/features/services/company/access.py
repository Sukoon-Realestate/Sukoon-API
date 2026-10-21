from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from ...company_models import Company, CompanyMembership, CompanyHousingRequest
from ..rental_phase2 import RentalConflict


def require_new_business():
    if not getattr(settings, "COMPANY_HOUSING_ENABLED", False):
        raise RentalConflict(
            "New company housing bookings are unavailable.",
            code="capability_unavailable",
        )


def member_for(user, company, action="read"):

    if not user or not user.is_active:
        raise PermissionDenied("An active account is required.")
    member = get_object_or_404(
        CompanyMembership, company=company, user=user, is_active=True
    )
    allowed = {
        "read": True,
        "admin": member.is_admin,
        "coordinate": member.is_coordinator,
        "approve": member.is_approver,
        "pay": member.can_execute_payments,
        "sign": bool(
            member.signing_verified_until
            and member.signing_verified_until > timezone.now()
        ),
    }
    if allowed.get(action) is not True:
        raise PermissionDenied(
            "Your company membership does not authorize this action."
        )
    return member


def company_for(user, identity, action="read", lock=False):
    query = Company.objects.select_for_update() if lock else Company.objects
    company = get_object_or_404(query, id=identity)
    member_for(user, company, action)
    return company


def request_for(user, identity, action="coordinate", lock=False):
    request = get_object_or_404(CompanyHousingRequest, id=identity)
    company = company_for(user, request.company.id, action, lock=lock)
    if lock:
        # Reassignment holds the company lock. Check the request loaded after
        # acquiring it, not an assignment read while another writer still ran.
        request = CompanyHousingRequest.objects.select_for_update().get(pk=request.pk)
    if action == "coordinate" and request.coordinator_id != user.pk:
        raise PermissionDenied("Only the assigned coordinator can manage this request.")
    request.company = company
    return request


def company_subject(user, identifier):
    from django.db.models import Q

    from .tenancy_access import visible

    from ...company_saved_models import CompanySavedList
    saved = CompanySavedList.objects.filter(id=identifier).first()
    if saved:
        from .saved_lists import authorize
        authorize(user, saved.company.id)
        return saved
    tenancy = visible(user).filter(id=identifier).first()
    if tenancy:
        return tenancy
    from ...company_contract_models import CompanyMandate, CompanyContractPreparation
    from .contract_access import can_read

    preparation = CompanyContractPreparation.objects.filter(id=identifier).first()
    if preparation and can_read(preparation, user):
        return preparation
    mandate = CompanyMandate.objects.filter(id=identifier).first()
    if (
        mandate
        and CompanyMembership.objects.filter(
            company=mandate.company, user=user, is_active=True
        )
        .filter(Q(is_admin=True) | Q(is_coordinator=True) | Q(pk=mandate.membership_id))
        .exists()
    ):
        return mandate
    from ...company_models import CompanyBookingItem, CompanyInvitation, PortfolioOffer
    from core_apps.properties.models import (
        ResidentialBuilding,
        ResidentialComplex,
        PortfolioBatch,
        PortfolioChangeSet,
        ResidentialMedia,
    )
    from django.db.models import Q
    from ...company_staff_models import (
        CompanyStaffRecord,
        CompanyStaffBatch,
        CompanyAccountProvisioning,
        CompanyWorkContactProof,
    )

    for model in (CompanyStaffRecord, CompanyStaffBatch):
        item = model.objects.filter(
            id=identifier,
            company__memberships__user=user,
            company__memberships__is_active=True,
            company__memberships__is_admin=True,
        ).first()
        if item:
            return item
    provisioning = CompanyAccountProvisioning.objects.filter(
        id=identifier, consumed_by=user
    ).first()
    if provisioning:
        return provisioning
    proof = CompanyWorkContactProof.objects.filter(id=identifier, user=user).first()
    if proof:
        return proof

    for model in (ResidentialBuilding, ResidentialComplex):
        item = model.objects.filter(id=identifier, manager=user).first()
        if item:
            return item
    batch = PortfolioBatch.objects.filter(id=identifier, owner=user).first()
    if batch:
        return batch
    for model in (PortfolioChangeSet, ResidentialMedia):
        item = model.objects.filter(id=identifier, owner=user).first()
        if item:
            return item
    offer = PortfolioOffer.objects.filter(id=identifier, owner=user).first()
    if offer:
        return offer
    member = (
        CompanyMembership.objects.filter(id=identifier)
        .select_related("company")
        .first()
    )
    if member and (
        member.user_id == user.pk
        or member.company.memberships.filter(
            user=user, is_active=True, is_admin=True
        ).exists()
    ):
        return member
    invitation = CompanyInvitation.objects.filter(
        id=identifier,
        invited_by=user,
        company__memberships__user=user,
        company__memberships__is_active=True,
        company__memberships__is_admin=True,
    ).first()
    if invitation:
        return invitation
    company = Company.objects.filter(
        id=identifier, memberships__user=user, memberships__is_active=True
    ).first()
    if company:
        return company
    administrative_item = CompanyBookingItem.objects.filter(
        id=identifier,
        request__company__memberships__user=user,
        request__company__memberships__is_active=True,
        request__company__memberships__is_admin=True,
    ).first()
    if administrative_item:
        return administrative_item
    for model, relation in [
        (CompanyHousingRequest, "company"),
        (CompanyBookingItem, "request__company"),
    ]:
        qs = model.objects.filter(id=identifier)
        qs = qs.filter(
            Q(**{relation + "__memberships__is_coordinator": True})
            | Q(**{relation + "__memberships__is_approver": True}),
            **{
                relation + "__memberships__user": user,
                relation + "__memberships__is_active": True,
            }
        )
        if model == CompanyHousingRequest:
            qs = qs.filter(Q(coordinator=user) | Q(items__assigned_approver__user=user))
        else:
            qs = qs.filter(
                Q(request__coordinator=user) | Q(assigned_approver__user=user)
            )
        item = qs.first()
        if item:
            return item
    return None


def authority_review_subject(user, identifier):
    """Receipt recovery for staff reviews without granting company membership.

    Operation lookup still scopes the receipt to its initiating actor. This
    resolver is intentionally separate from owner/company action capabilities.
    """
    from core_apps.properties.models import (
        ResidentialBuilding,
        ResidentialComplex,
        ResidentialMedia,
    )
    from ..rental_lifecycle.common import staff_role
    from ...models import CompanyMandate

    mandate = CompanyMandate.objects.filter(id=identifier).first()
    if mandate and staff_role(
        user, {"kyc_reviewer"} if mandate.kind == "sign" else {"financial_approver"}
    ):
        return mandate

    for model, roles in (
        (Company, {"kyc_reviewer"}),
        (ResidentialBuilding, {"property_reviewer"}),
        (ResidentialComplex, {"property_reviewer"}),
        (ResidentialMedia, {"property_reviewer"}),
    ):
        if staff_role(user, roles):
            item = model.objects.filter(id=identifier).first()
            if item:
                return item
    return None


def actions(user, capability, identifier=""):
    from ...company_models import CompanyBookingItem

    if not identifier:
        if capability == "residential_portfolios":
            return ["read", "create", "batch", "offer"]
        return ["read", "join", "activate"] + (
            ["create"] if getattr(settings, "COMPANY_HOUSING_ENABLED", False) else []
        )
    item = company_subject(user, identifier)
    if item is None:
        return []
    from ...models import CompanyTenancy

    if isinstance(item, CompanyTenancy):
        from .tenancy_projection import payload

        return ["read"] + payload(item, user)["actions"]
    from ...company_contract_models import CompanyMandate, CompanyContractPreparation

    if isinstance(item, CompanyContractPreparation):
        from .contract_projection import payload

        view = payload(item, user)
        return (
            ["read"]
            + (["contract_respond"] if view["responses"] else [])
            + (["contract_withdraw"] if view["can_withdraw"] else [])
            + (["contract_reserve"] if view["can_reserve"] else [])
            + (["contract_agreement"] if view["can_create_agreement"] else [])
        )
    if isinstance(item, CompanyMandate):
        from .mandates import payload

        return ["read"] + [
            "mandate_" + action for action in payload(item, user)["actions"]
        ]
    if capability == "residential_portfolios":
        return [
            "read",
            "batch",
            "offer",
            "publish",
            "pause",
            "attach",
            "edit",
            "preview",
            "apply",
            "media",
            "remove_media",
        ]
    company = (
        item
        if isinstance(item, Company)
        else (
            item.request.company
            if isinstance(item, CompanyBookingItem)
            else getattr(item, "company", None)
        )
    )
    if company is None:
        return []
    member = CompanyMembership.objects.filter(
        company=company, user=user, is_active=True
    ).first()
    if member is None:
        return []
    result = ["read"]
    if member.is_admin or member.is_coordinator:
        result += ["saved_lists"]
    if member.is_admin:
        result += [
            "mandate_propose",
            "invite",
            "update_member",
            "budget",
            "reassign",
            "staff",
            "activation",
            "revoke",
            "approval_route",
        ]
    if member.is_coordinator:
        result += ["withdraw"]
    if getattr(settings, "COMPANY_HOUSING_ENABLED", False):
        if member.is_coordinator:
            result += [
                "create_request",
                "edit_request",
                "select",
                "hold",
                "submit",
                "prepare_contract",
            ]
        if member.is_approver:
            if (
                isinstance(item, CompanyBookingItem)
                and item.status == "approval_pending"
                and item.assigned_approver_id
                and item.assigned_approver.user_id == user.pk
            ):
                from .approval_routing import eligible

                if eligible(item.assigned_approver, item):
                    result += ["decide"]
    return result
