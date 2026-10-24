"""Company billing authority is checked against current membership and mandates."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..models import Company, CompanyMembership, CompanyMandate


def organization_for(user, identity, *, lock=False, pay=False, amount=0):
    if not identity:
        return None
    from rest_framework import serializers

    field = serializers.UUIDField()
    identity = field.run_validation(identity)
    query = Company.objects.select_for_update() if lock else Company.objects
    company = get_object_or_404(query, id=identity)
    member = CompanyMembership.objects.filter(
        company=company, user=user, is_active=True
    ).first()
    if (
        not user.is_active
        or member is None
        or not (member.is_admin or member.can_execute_payments)
    ):
        raise PermissionDenied(
            {
                "message": "Current company billing authority is required.",
                "code": "organization_permission_revoked",
            }
        )
    if pay:
        from .company.tenancy_access import execution_mandate

        if not member.can_execute_payments or not any(
            execution_mandate(m, exposure=amount)
            for m in CompanyMandate.objects.filter(
                company=company, membership=member, kind="pay"
            ).select_related("membership__user")
        ):
            raise PermissionDenied(
                {
                    "message": "A current independently verified payment mandate is required.",
                    "code": "organization_permission_revoked",
                }
            )
        if (
            company.budget_limit_minor is not None
            and amount > company.budget_limit_minor
        ):
            raise ValidationError(
                {"organization_id": "The purchase exceeds the company budget."}
            )
    return company
