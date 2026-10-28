"""HTTP entry-point policy, in addition to resource and command authorization."""

from rest_framework.exceptions import PermissionDenied
from .role_context import http_context, ROLES


def authorize(request, function):
    module = function.__module__.rsplit(".", 1)[-1]
    name = function.__name__
    current = http_context(request.user)
    if current is None:
        return
    role = request.headers.get("X-Sukoon-Company-Role", "")
    # Discovery and platform/owner functions do not reveal company execution data.
    discovery = {
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
    if name in discovery.get(module, set()):
        return
    rules = {
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
            "rental_summary": {
                "coordinator",
                "approver",
                "signer",
                "payer",
                "employee",
            },
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
    allowed = rules.get(module, {}).get(name)
    if allowed is not None and role not in allowed:
        raise PermissionDenied(
            "Choose the company role assigned to this work.",
            code="company_role_forbidden",
        )
    # These legacy discussions contain mixed approval/commercial history. Until
    # every message has a verified role audience, no role may read or post here.
    if module == "company_chat_views":
        raise PermissionDenied(
            "This discussion has no verified role audience.",
            code="company_role_audience_required",
        )
