"""Explicit per-relationship company review permissions, checked on every use."""

from django.utils import timezone
from rest_framework.exceptions import NotFound
from ...models import CompanyMembership, CompanyReviewAuthority
from .policy import ReviewError, require_actor


def membership(user, company, *, signer=False, admin=False, lock=False):

    require_actor(user)
    query = (
        CompanyMembership.objects.select_for_update()
        if lock
        else CompanyMembership.objects
    )
    member = query.filter(company=company, user=user, is_active=True).first()
    if not member or not user.is_verified:
        raise NotFound()
    if admin and not member.is_admin:
        raise NotFound()
    if signer and (
        company.review_status != "verified"
        or not member.signing_verified_until
        or member.signing_verified_until <= timezone.now()
    ):
        raise ReviewError("company_signing_authority_required", 403)
    return member


def permitted(user, binding, company, *, submit=False, history=False, lock=False):

    if not binding or binding.state != "accepted" or not company:
        return False
    if company.pk not in {binding.renter_company_id, binding.landlord_company_id}:
        return False
    if (
        not user
        or not user.is_authenticated
        or not user.is_active
        or not user.is_verified
    ):
        return False
    if lock:
        from ...models import Company
        from django.contrib.auth import get_user_model

        Company.objects.select_for_update().get(pk=company.pk)
        current_user = get_user_model().objects.get(pk=user.pk)
        if not current_user.is_active or not current_user.is_verified:
            return False
        # Company membership mutations lock the company before its members.
        # Keep that same order instead of locking joined rows in planner order.
        CompanyMembership.objects.select_for_update().filter(
            company=company, user=user
        ).first()
    query = (
        CompanyReviewAuthority.objects.select_for_update()
        if lock
        else CompanyReviewAuthority.objects
    )
    authority = (
        query.select_related("membership", "membership__company")
        .filter(
            binding=binding,
            membership__company=company,
            membership__user=user,
            membership__is_active=True,
            is_active=True,
        )
        .first()
    )
    if (
        not authority
        or (submit and not authority.can_submit)
        or (history and not authority.can_view_reputation)
    ):
        return False
    return not submit or authority.membership.company.review_status == "verified"


def require_opportunity(user, opportunity, *, submit=False, lock=False):
    company = opportunity.reviewer_company
    if not permitted(
        user, opportunity.case.company_binding, company, submit=submit, lock=lock
    ):
        raise NotFound()
    if submit:
        case = opportunity.case
        binding = case.company_binding
        opposite = (
            binding.landlord_company
            if company.pk == binding.renter_company_id
            else binding.renter_company
        )
        counterpart = (
            case.party_b_id
            if company.pk == binding.renter_company_id
            else case.party_a_id
        )
        if user.pk == counterpart or (
            opposite
            and CompanyMembership.objects.filter(
                company=opposite, user=user, is_active=True
            ).exists()
        ):
            raise ReviewError("conflict_of_interest")
        if (
            binding.booking_id
            and binding.booking.assignments.filter(
                employee=user, occupancy_confirmations__state="accepted"
            ).exists()
        ):
            raise ReviewError("conflict_of_interest")
    return opportunity


def company_history(user, company_id):
    require_actor(user)
    return CompanyReviewAuthority.objects.filter(
        membership__company__id=company_id,
        membership__user=user,
        membership__is_active=True,
        is_active=True,
        can_view_reputation=True,
        binding__state="accepted",
    ).exists()


def accessible_company_opportunities(user, company_id):
    from ...models import ReviewOpportunity

    return ReviewOpportunity.objects.filter(
        reviewer_company__id=company_id,
        case__company_binding__review_authorities__membership__company__id=company_id,
        case__company_binding__review_authorities__membership__user=user,
        case__company_binding__review_authorities__membership__is_active=True,
        case__company_binding__review_authorities__is_active=True,
        case__company_binding__review_authorities__can_submit=True,
    ).distinct()


def recipients(binding, company, *, submit=False):
    from django.contrib.auth import get_user_model

    if not binding or not company:
        return []
    rows = CompanyReviewAuthority.objects.filter(
        binding=binding,
        membership__company=company,
        membership__is_active=True,
        membership__user__is_active=True,
        is_active=True,
    )
    if submit:
        rows = rows.filter(can_submit=True)
    return list(
        get_user_model().objects.filter(pk__in=rows.values("membership__user_id"))
    )
