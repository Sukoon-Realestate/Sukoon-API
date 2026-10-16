from django.utils import timezone
from .access import member_for


def membership_payload(member):
    return {
        "id": str(member.id),
        "user_id": str(member.user.id),
        "name": member.user.get_full_name,
        "revision": member.revision,
        "is_active": member.is_active,
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


def company_payload(company, user):
    member = member_for(user, company)
    result = {
        "id": str(company.id),
        "revision": company.revision,
        "name": company.name,
        "review_status": company.review_status,
        "membership": membership_payload(member),
        "permissions": {
            "manage_people": member.is_admin,
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
        )
    if member.is_admin or member.is_approver:
        from django.db.models import Q, Sum

        rows = company.budget_reservations.filter(
            Q(status="committed")
            | Q(status="reserved", approval__expires_at__gt=timezone.now())
        )
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
    return result
