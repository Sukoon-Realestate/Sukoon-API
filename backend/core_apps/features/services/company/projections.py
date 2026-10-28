from django.utils import timezone
from .access import member_for


def membership_payload(member):
    from core_apps.users.services.new_business import restricted_accounts

    return {
        "id": str(member.id),
        "user_id": str(member.user.id),
        "name": member.user.get_full_name,
        "revision": member.revision,
        "is_active": member.is_active,
        "account_closure_blocked": bool(restricted_accounts(member.user_id)),
        "roles": [
            role
            for role in ("admin", "coordinator", "approver", "employee")
            if getattr(member, "is_" + role)
        ],
        "can_execute_payments": member.can_execute_payments,
        "signing_verified": bool(
            member.signing_verified_until
            and member.signing_verified_until > timezone.now()
        ),
    }


def company_payload(company, user, *, discovery_only=False):
    from .role_context import http_context, discovery, selected
    from ...company_models import CompanyMembership

    if http_context(user) is not None:
        current = CompanyMembership.objects.get(
            company=company, user=user, is_active=True
        )
        role = "" if discovery_only else selected(user, company, required=False)
        if not role:
            return discovery(company, current)
    member = member_for(user, company)
    from ...models import CompanyTenancy
    from django.db.models import Q

    cost_access = (
        member.is_admin
        or member.is_coordinator
        or member.is_approver
        or CompanyTenancy.objects.filter(
            lease__renter_company=company,
        )
        .filter(
            Q(signer_mandate__membership=member) | Q(payer_mandate__membership=member)
        )
        .exclude(lease__private_access_revocations__user=user)
        .exists()
    )
    result = {
        "id": str(company.id),
        "revision": company.revision,
        "name": company.name,
        "review_status": company.review_status,
        "membership": membership_payload(member),
        "permissions": {
            "view_costs": cost_access,
            "manage_people": member.is_admin,
            "manage_budget": member.is_admin,
            "coordinate": member.is_coordinator,
            "approve": member.is_approver,
            "execute_payment": member.can_execute_payments,
            "sign": bool(
                member.signing_verified_until
                and member.signing_verified_until > timezone.now()
            ),
        },
    }
    if member.is_admin:
        result.update(
            registration_number=company.registration_number,
            contact_email=company.contact_email,
            default_approver_id=(
                str(company.default_approver.id)
                if company.default_approver_id
                else None
            ),
            backup_approver_id=(
                str(company.backup_approver.id) if company.backup_approver_id else None
            ),
            default_approver_name=(
                company.default_approver.user.get_full_name
                if company.default_approver_id
                else ""
            ),
            backup_approver_name=(
                company.backup_approver.user.get_full_name
                if company.backup_approver_id
                else ""
            ),
        )
    result["readiness"] = {
        "company_review": company.review_status,
        "independent_approver_configured": bool(
            company.default_approver_id
            and company.default_approver.is_active
            and company.default_approver.is_approver
        ),
        "signing_authority": company.memberships.filter(
            is_active=True, signing_verified_until__gt=timezone.now()
        ).exists(),
        "payment_executor": company.memberships.filter(
            is_active=True, can_execute_payments=True
        ).exists(),
        "corporate_contracting": False,
        "contract_preparation": True,
        "corporate_payments": False,
    }
    if member.is_admin or member.is_approver:
        from django.db.models import Q, Sum

        rows = company.budget_reservations.filter(
            Q(status="committed")
            | Q(status="reserved", approval__expires_at__gt=timezone.now())
        )
        from .listing_changes import live_budget

        rows = live_budget(rows)
        result.update(
            budget_limit_minor=company.budget_limit_minor,
            deposit_limit_minor=company.deposit_limit_minor,
            reserved_rent_minor=rows.filter(status="reserved").aggregate(
                value=Sum("rent_minor")
            )["value"]
            or 0,
            committed_rent_minor=rows.filter(status="committed").aggregate(
                value=Sum("rent_minor")
            )["value"]
            or 0,
            deposit_exposure_minor=rows.aggregate(value=Sum("deposit_minor"))["value"]
            or 0,
        )
    from .role_projections import company as project_company

    return project_company(result, company, user)
