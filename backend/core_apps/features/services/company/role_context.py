"""An HTTP company role narrows authority; it never grants it.

Internal jobs retain their explicit service authorization. Every HTTP request,
including shared rental/document routes, has a context even without headers.
Company discovery returns a separate minimal projection before role selection.
"""

from contextvars import ContextVar
from contextlib import contextmanager
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, NotFound
from django.http import Http404

_request = ContextVar("sukoon_company_request", default=None)
ROLES = ("admin", "coordinator", "approver", "signer", "payer", "employee")
RESOURCE_ROLES = {
    "administrator": "admin",
    "coordinator": "coordinator",
    "new_coordinator": "coordinator",
    "approver": "approver",
    "signer": "signer",
    "new_signer": "signer",
    "prior_signer": "signer",
    "payer": "payer",
    "new_payer": "payer",
    "employee": "employee",
    "incoming_employee": "employee",
    "outgoing_employee": "employee",
}


def resource_role(role):
    if role.startswith("resident_"):
        return "employee"
    if role.startswith("prior_signer_"):
        return "signer"
    return RESOURCE_ROLES.get(role, "")


class CompanyRoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _request.set(request)
        try:
            return self.get_response(request)
        finally:
            _request.reset(token)


@contextmanager
def system_context():
    """Event recipient discovery is independent of the initiating role."""
    token = _request.set(None)
    try:
        yield
    finally:
        _request.reset(token)


def http_context(user=None):
    request = _request.get()
    if request is None:
        return None
    return request


@contextmanager
def bound_role(user, company_id, role):
    """Only for verified signed documents and persisted event destinations.

    A binding narrows the subsequent ordinary resource authorization. It does
    not bypass current membership, mandate or assignment validation.
    """
    from types import SimpleNamespace

    token = _request.set(
        SimpleNamespace(
            user=user,
            headers={
                "X-Sukoon-Company-Id": str(company_id),
                "X-Sukoon-Company-Role": role,
            },
        )
    )
    try:
        yield
    finally:
        _request.reset(token)


def available(member):
    if not member.is_active or not member.user.is_active:
        return []
    result = [
        r for r in ("admin", "coordinator", "approver") if getattr(member, "is_" + r)
    ]
    # A named viewing representative works in coordination, but their resource
    # access remains limited to that appointment; this grants no member flag.
    from core_apps.properties.models import PropertyVisit

    if (
        "coordinator" not in result
        and PropertyVisit.objects.filter(
            company=member.company,
            tenant=member.user,
            status__in=["pending", "confirmed"],
        ).exists()
    ):
        result.append("coordinator")
    from .mandates import current

    for kind, role in (("sign", "signer"), ("pay", "payer")):
        if any(
            current(m)
            for m in member.company.mandates.filter(
                membership=member, kind=kind, state="approved"
            ).select_related("membership__user")
        ):
            result.append(role)
    staff = getattr(member, "staff_record", None)
    if member.is_employee and (staff is None or staff.employment_status == "active"):
        result.append("employee")
    return result


def selected(user, company, *, required=True):
    request = http_context(user)
    if request is None:
        return None
    role = request.headers.get("X-Sukoon-Company-Role", "")
    identity = request.headers.get("X-Sukoon-Company-Id", "")
    if not role and not required:
        return ""
    if role not in ROLES or not identity or identity != str(company.id):
        raise PermissionDenied(
            "Choose a current role for this company.", code="company_role_required"
        )
    from ...company_models import CompanyMembership

    member = get_object_or_404(
        CompanyMembership, company=company, user=user, is_active=True
    )
    if role not in available(member):
        raise PermissionDenied(
            "This company role is no longer available.", code="company_role_revoked"
        )
    return role


def require(user, company, roles):
    role = selected(user, company)
    if role is not None and role not in roles:
        raise PermissionDenied(
            "Switch to an authorized role for this action.",
            code="company_role_forbidden",
        )
    return role


def permits(member, role):
    """Use for the viewer, never for another member's eligibility."""
    current = selected(member.user, member.company)
    if current is not None:
        return current == role
    return role in available(member)


def narrow(user, company, roles):
    request = http_context(user)
    if request is None:
        return roles
    # Owners and platform reviewers have separate authority outside a company
    # context. Selecting a company role does not inherit their other roles.
    if not request.headers.get("X-Sukoon-Company-Role"):
        return set(roles) & {"owner", "new_owner", "financial_reviewer"}
    try:
        current = selected(user, company)
    except (PermissionDenied, NotFound, Http404):
        return set()
    return {r for r in roles if resource_role(r) == current}


def discovery(company, member):
    return {
        "id": str(company.id),
        "name": company.name,
        "revision": company.revision,
        "membership": {
            "id": str(member.id),
            "revision": member.revision,
            "is_active": member.is_active,
        },
        "role_selection_required": True,
    }


def context_payload(company, user):
    from ...company_models import CompanyMembership

    member = get_object_or_404(
        CompanyMembership, company=company, user=user, is_active=True
    )
    return {
        "company_id": str(company.id),
        "company_name": company.name,
        "membership_id": str(member.id),
        "authorization_revision": member.revision,
        "roles": [{"role": role} for role in available(member)],
    }
