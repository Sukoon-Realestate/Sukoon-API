from rest_framework.response import Response
from .company_views import company_api, mutate, page
from .company_serializers import CommandBody
from .company_tenancy_serializers import ExecutionAuthorityBody, command_body
from .rental_lifecycle_views.common import validated
from .services.company import (
    tenancy_commercial as commercial,
    tenancy_continuation_signing as continuation,
    tenancy_ownership as ownership,
    tenancy_resolution as resolution,
    tenancy_adjustments as adjustments,
    tenancy_access as access,
    tenancy_contracts as contracts,
    tenancy_changes as changes,
    tenancy_closure as closure,
    tenancy_occupancy as occupancy,
    tenancy_maintenance as maintenance,
    tenancy_projection as projection,
)
from .services.company.contract_access import get as preparation_for
from .services.rental_lifecycle.common import require_revision, require_staff


@company_api(["POST"])
def create(request, preparation_id):
    body = validated(CommandBody, request.data)

    def authorize():
        from .services.company.contract_access import manages
        from rest_framework.exceptions import PermissionDenied

        item = preparation_for(request.user, preparation_id, lock=True)
        if not manages(item, request.user):
            raise PermissionDenied(
                "Only the currently assigned coordinator can create this agreement."
            )
        return item

    return mutate(
        request,
        "company.tenancy.create",
        authorize,
        lambda _: contracts.create(request.user, preparation_id, body),
        receipt_resource,
        creating=True,
    )


@company_api(["GET"])
def collection(request):
    from .services.rental_lifecycle.common import require_actor

    require_actor(request.user)
    query = access.visible(request.user)
    if request.query_params.get("company_id"):
        from rest_framework import serializers

        identity = serializers.UUIDField().run_validation(
            request.query_params["company_id"]
        )
        query = query.filter(lease__renter_company__id=identity)
    return page(request, query, lambda item: projection.payload(item, request.user))


@company_api(["GET"])
def detail(request, tenancy_id):
    return Response(
        projection.payload(access.get(request.user, tenancy_id), request.user)
    )


def open_case(item, user, data):
    from .services.rental_lifecycle.cases import open_system_case

    open_system_case(
        kind="company_tenancy_review",
        source_key=f"company-tenancy:{item.id}:{user.id}",
        actor=user,
        lease=item.lease,
        reason=data["reason"],
        next_action="Review the exact company tenancy, current authority and outstanding possession or financial obligations.",
    )
    return access.changed(item, user, "company_tenancy_escalated", data["reason"])


HANDLERS = {
    "commercial_change": commercial.propose,
    "ownership_change": ownership.propose,
    "settlement_adjustment": adjustments.propose,
    "submit_continuation": continuation.submit,
    "sign_continuation": continuation.sign,
    "resume_continuation": continuation.resume,
    "release_continuation": resolution.propose,
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


@company_api(["POST"])
def action(request, tenancy_id, action):
    body = command_body(action, request.data)

    def authorize():
        item = access.get(request.user, tenancy_id, lock=True)
        authorize_action(item, request.user, action, body)
        return item

    def execute(item):
        require_revision(item.lease, body["expected_revision"])
        return HANDLERS[action](item, request.user, body)

    return mutate(
        request, "company.tenancy." + action, authorize, execute, receipt_resource
    )


def receipt_resource(item):
    # A receipt proves the original effect, not permission to redisclose its old
    # commercial/roster projection. Screens refresh the current authorized view.
    return {"id": str(item.id), "revision": item.revision}


def authorize_action(item, user, action, body):
    """Reauthorize receipts as well as new effects after a responsibility changes."""
    from django.shortcuts import get_object_or_404
    from rest_framework.exceptions import PermissionDenied
    from .models import (
        CompanyTenancyChange,
        EmployeeAssignment,
        EmployeeOccupancyConfirmation,
    )

    permissions = {
        "commercial_change": {"owner", "signer"},
        "ownership_change": {"owner", "signer"},
        "settlement_adjustment": {"owner", "payer"},
        "submit_continuation": {"owner"},
        "resume_continuation": {"owner", "coordinator", "signer", "payer"},
        "release_continuation": {"owner", "signer"},
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
        elif user.pk != change.proposed_by_id and "coordinator" not in access.roles(
            item, user
        ):
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
        from .models import CompanyMaintenanceScope

        prop = body.get("property_id")
        if action == "maintenance_action":
            prop = get_object_or_404(
                CompanyMaintenanceScope,
                tenancy=item,
                request__id=body["maintenance_id"],
            ).property.id
        if (
            not access.roles(item, user) & {"owner", "coordinator", "payer"}
            and not item.preparation.booking.assignments.filter(
                employee=user, property__id=prop, occupancy_status="occupied"
            ).exists()
        ):
            raise PermissionDenied(
                "This maintenance record is outside your current responsibility."
            )


@company_api(["POST"])
def verify_mandate(request, mandate_id):
    from .models import CompanyMandate
    from django.shortcuts import get_object_or_404

    body = validated(ExecutionAuthorityBody, request.data)

    def authorize():
        item = get_object_or_404(CompanyMandate, id=mandate_id)
        require_staff(
            request.user,
            {"kyc_reviewer"} if item.kind == "sign" else {"financial_approver"},
        )
        return item

    return mutate(
        request,
        "company.mandate.execution_review",
        authorize,
        lambda _: contracts.verify_mandate(request.user, mandate_id, body),
        lambda item: {
            "id": str(item.id),
            "revision": item.revision,
            "state": item.state,
            "execution_verified_until": item.execution_verified_until.isoformat(),
        },
    )
