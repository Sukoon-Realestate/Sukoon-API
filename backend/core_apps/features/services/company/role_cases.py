"""Do not expose legacy mixed operational discussions through company roles."""

from django.http import Http404
from rest_framework.exceptions import PermissionDenied, NotFound
from .role_context import http_context, selected


def company_for(case):
    if case.lease_id and case.lease.renter_company_id:
        return case.lease.renter_company
    if case.housing_request_id:
        return case.housing_request.company
    if case.payment_attempt_id and case.payment_attempt.invoice.organization_id:
        return case.payment_attempt.invoice.organization
    return None


def can_read(case, user):
    company = company_for(case)
    request = http_context(user)
    if company is None or request is None:
        return True
    if not request.headers.get("X-Sukoon-Company-Role"):
        # Independent owners/platform operators retain their existing access;
        # membership and having opened a case alone never restore a role.
        from ..rental_lifecycle.cases import independent_case_operator

        return bool(
            case.lease_id
            and case.lease.owner_id == user.pk
            or case.opened_by_id == user.pk
            and case.baseline.get("independent_owner_id") == str(user.id)
            or independent_case_operator(case, user)
        )
    try:
        role = selected(user, company)
    except (PermissionDenied, NotFound, Http404):
        return False
    if case.kind == "service_activation":
        from ..fulfillment_cases import can_read_invoice

        return role == "payer" and can_read_invoice(case, user)
    if case.kind == "company_sourcing":
        return role == "coordinator" and case.housing_request.coordinator_id == user.pk
    return case.opened_by_id == user.pk and case.baseline.get("company_role") == role


def restrict(query, user):
    if http_context(user) is None:
        return query
    denied = [
        row.pk
        for row in query.select_related(
            "lease__renter_company",
            "housing_request__company",
            "payment_attempt__invoice__organization",
        )
        if not can_read(row, user)
    ]
    return query.exclude(pk__in=denied)
