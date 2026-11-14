"""Company tenancy commands and replay authorization, independent of HTTP names."""

from . import (
    tenancy_commercial as commercial,
    tenancy_continuation_signing as continuation,
    tenancy_ownership as ownership,
    tenancy_resolution as resolution,
    tenancy_initial_recovery as initial_recovery,
    tenancy_adjustments as adjustments,
    tenancy_access as access,
    tenancy_contracts as contracts,
    tenancy_changes as changes,
    tenancy_closure as closure,
    tenancy_occupancy as occupancy,
    tenancy_maintenance as maintenance,
    service_requests,
)
from .contract_access import get as preparation_for
from ..rental_lifecycle.common import command, require_revision, require_staff


def open_case(item, user, data):
    from ..rental_lifecycle.cases import open_system_case
    from .role_context import selected

    role = selected(user, item.lease.renter_company, required=False) or "owner"
    open_system_case(
        kind="company_tenancy_review",
        source_key=f"company-tenancy:{item.id}:{user.id}:{role}",
        actor=user,
        lease=item.lease,
        reason=data["reason"],
        next_action="Review the exact company tenancy, current authority and outstanding possession or financial obligations.",
    )
    return access.changed(item, user, "company_tenancy_escalated", data["reason"])


HANDLERS = {
    "request_service": service_requests.request,
    "commercial_change": commercial.propose,
    "ownership_change": ownership.propose,
    "settlement_adjustment": adjustments.propose,
    "submit_continuation": continuation.submit,
    "sign_continuation": continuation.sign,
    "resume_continuation": continuation.resume,
    "release_continuation": resolution.propose,
    "release_agreement": initial_recovery.propose,
    "review": contracts.review,
    "submit_signature": contracts.submit,
    "sign": contracts.signing_session,
    "cancel": contracts.cancel,
    "handover": occupancy.propose_handover,
    "presence": occupancy.propose_presence,
    "presence_respond": occupancy.confirm_presence,
    "replace_employee": occupancy.propose_replacement,
    "respond_change": changes.respond,
    "withdraw_change": changes.withdraw,
    "resume_change": changes.resume,
    "terminate": closure.propose_termination,
    "settlement": closure.propose_settlement,
    "replace_authority": closure.propose_authority,
    "maintenance": maintenance.create,
    "maintenance_action": maintenance.act,
    "reconcile": closure.reconcile,
    "open_case": open_case,
}


def receipt_resource(item):
    return {"id": str(item.id), "revision": item.revision}


def authorize_action(item, user, action, body):
    """Reauthorize receipts as well as new effects after a responsibility changes."""
    from django.shortcuts import get_object_or_404
    from rest_framework.exceptions import PermissionDenied
    from ...models import (
        CompanyTenancyChange,
        EmployeeAssignment,
        EmployeeOccupancyConfirmation,
    )

    if action == "request_service":
        service_requests.authorize_request(item, user, body.get("kind"))
    permissions = {
        "commercial_change": {"owner", "signer"},
        "ownership_change": {"owner", "signer"},
        "settlement_adjustment": {"owner", "payer"},
        "submit_continuation": {"owner"},
        "resume_continuation": {"owner", "coordinator", "signer", "payer"},
        "release_continuation": {"owner", "signer"},
        "release_agreement": {"owner", "signer"},
        "review": {body.get("role")},
        "submit_signature": {"owner"},
        "sign": {"owner", "signer"},
        "cancel": {"owner", "coordinator"},
        "handover": {"owner", "coordinator"},
        "replace_employee": {"coordinator"},
        "terminate": {"owner", "signer"},
        "settlement": {"owner", "payer"},
        "replace_authority": {"administrator"},
        "resume_change": {"coordinator"},
        "reconcile": {"owner", "coordinator", "signer", "payer"},
    }
    if action in permissions:
        access.require_role(item, user, permissions[action])
    if action in {"respond_change", "withdraw_change", "sign_continuation"}:
        change = get_object_or_404(
            CompanyTenancyChange, tenancy=item, id=body["change_id"]
        )
        if action in {"respond_change", "sign_continuation"}:
            changes.authorize_role(item, change, user, body["role"], positive=False)
        elif not changes.can_withdraw(item, change, user):
            raise PermissionDenied(
                "Only the proposer or current coordinator can withdraw this review."
            )
    if action in {"presence", "presence_respond"}:
        row = (
            get_object_or_404(
                EmployeeAssignment,
                item=item.preparation.booking,
                id=body["assignment_id"],
            )
            if action == "presence"
            else get_object_or_404(
                EmployeeOccupancyConfirmation,
                assignment__item=item.preparation.booking,
                id=body["confirmation_id"],
            ).assignment
        )
        if user.pk not in {row.employee_id, item.lease.owner_id}:
            raise PermissionDenied(
                "Only the actual employee or owner can confirm this stay."
            )
    if action in {"maintenance", "maintenance_action"}:
        from ...models import CompanyMaintenanceScope

        prop = body.get("property_id")
        if action == "maintenance_action":
            prop = get_object_or_404(
                CompanyMaintenanceScope,
                tenancy=item,
                request__id=body["maintenance_id"],
            ).property.id
        if not access.roles(item, user) & {"owner", "coordinator", "payer"} and (
            not item.preparation.booking.assignments.filter(
                employee=user, property__id=prop, occupancy_status="occupied"
            ).exists()
        ):
            raise PermissionDenied(
                "This maintenance record is outside your current responsibility."
            )


def create_agreement(user, preparation_id, body, receipt_data):
    from .contract_preparation import existing_account_parties
    from .contract_access import manages
    from rest_framework.exceptions import PermissionDenied

    def authorize():
        item = preparation_for(user, preparation_id, lock=True)
        if not manages(item, user):
            raise PermissionDenied(
                "Only the currently assigned coordinator can create this agreement."
            )
        return item

    def execute(_):
        item = contracts.create(user, preparation_id, body)
        return item, receipt_resource(item), 201

    return command(
        user=user,
        operation="company.tenancy.create",
        data=receipt_data,
        authorize=authorize,
        execute=execute,
        account_parties=lambda: existing_account_parties(preparation_id),
    )


def apply_action(user, tenancy_id, action, body, receipt_data):
    def authorize():
        item = access.get(user, tenancy_id, lock=True)
        authorize_action(item, user, action, body)
        return item

    def execute(item):
        require_revision(item.lease, body["expected_revision"])
        changed = HANDLERS[action](item, user, body)
        return changed, receipt_resource(changed), 200

    return command(
        user=user,
        operation="company.tenancy." + action,
        data=receipt_data,
        authorize=authorize,
        execute=execute,
    )


def verify_execution_mandate(user, mandate_id, body, receipt_data):
    from ...models import CompanyMandate
    from django.shortcuts import get_object_or_404

    def authorize():
        item = get_object_or_404(CompanyMandate, id=mandate_id)
        require_staff(
            user, {"kyc_reviewer"} if item.kind == "sign" else {"financial_approver"}
        )
        return item

    def execute(_):
        item = contracts.verify_mandate(user, mandate_id, body)
        return (
            item,
            {
                "id": str(item.id),
                "revision": item.revision,
                "state": item.state,
                "execution_verified_until": item.execution_verified_until.isoformat(),
            },
            200,
        )

    return command(
        user=user,
        operation="company.mandate.execution_review",
        data=receipt_data,
        authorize=authorize,
        execute=execute,
    )
