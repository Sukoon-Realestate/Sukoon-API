"""Stable resource/action HTTP policy, additional to current resource authorization.

CBVs pass explicit metadata; the supported callable entry point remains for old
imports. Neither method names nor class names are authorization identities.
"""

from rest_framework.exceptions import PermissionDenied
from .role_context import http_context, ROLES

DISCOVERY = {
    "company_views": {
        "capabilities",
        "companies",
        "role_contexts",
        "accept_invitation",
        "invitation_detail",
    },
    "company_staff_views": {
        "contexts",
        "access_preview",
        "request_contact_proof",
        "verify_contact_proof",
        "access_response",
    },
}

RULES = {
    "company_views": {
        "company_detail": set(ROLES),
        "members": {"admin"},
        "member_action": {"admin"},
        "invitations": {"admin"},
        "housing_requests": {"coordinator", "approver"},
        "housing_request": {"coordinator", "approver"},
        "select_offer": {"coordinator"},
        "item_action": {"coordinator", "approver"},
    },
    "company_admin_views": {
        "company_budget": {"admin"},
        "occupants": {"coordinator"},
        "reassign_coordinator": {"admin"},
    },
    "company_work_views": {
        "approval_route": {"admin"},
        "reassign": {"admin"},
        "work": {"coordinator", "approver"},
    },
    "company_staff_views": {
        "planning_people": {"coordinator"},
        "roster": {"admin"},
        "detail": {"admin"},
        "activation": {"admin"},
        "batch": {"admin"},
        "batch_detail": {"admin"},
    },
    "company_rental_value_views": {
        "rental_summary": {"coordinator", "approver", "signer", "payer", "employee"},
        "housing_report": {"payer"},
        "import_preview": {"admin"},
        "assistance": {"coordinator"},
    },
    "company_saved_views": {
        n: {"coordinator"} for n in ("collection", "detail", "items", "action")
    },
    "company_contract_views": {
        "mandates": {"admin", "coordinator"},
        "mandate_action": {"admin", "signer", "payer"},
        "preparation": {"coordinator"},
    },
}


def authorize_policy(request, resource, action):
    if http_context(request.user) is None:
        return
    if action in DISCOVERY.get(resource, set()):
        return
    allowed = RULES.get(resource, {}).get(action)
    if (
        allowed is not None
        and request.headers.get("X-Sukoon-Company-Role", "") not in allowed
    ):
        raise PermissionDenied(
            "Choose the company role assigned to this work.",
            code="company_role_forbidden",
        )
    # Mixed legacy discussion audiences remain closed to every company role.
    if resource == "company_chat_views":
        raise PermissionDenied(
            "This discussion has no verified role audience.",
            code="company_role_audience_required",
        )


def authorize(request, function):
    """Compatibility for supported callers that still supply a callable."""
    cls = getattr(function, "view_class", None) or getattr(function, "cls", None)
    policies = getattr(cls, "action_policies", {})
    policy = policies.get(getattr(request, "method", "").lower())
    if policy is not None and policy.boundary == "company":
        return authorize_policy(request, policy.resource, policy.action)
    if any(item.boundary == "company" for item in policies.values()):
        # A CBV has no legacy callable policy key. An unsupported method must
        # never fall through to an unrecognized class name and gain access.
        raise PermissionDenied(
            "Choose the company role assigned to this work.",
            code="company_role_forbidden",
        )
    return authorize_policy(
        request, function.__module__.rsplit(".", 1)[-1], function.__name__
    )
