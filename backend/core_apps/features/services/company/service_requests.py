"""Operator preparation of rare changes; participants retain every decision."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from ...models import (
    CompanyTenancy,
    CompanyTenancyChange,
    RentalOperationalCase,
    FinalSettlement,
)
from ..rental_phase2 import RentalConflict
from ..rental_lifecycle.common import require_revision, require_actor, audit
from . import tenancy_access as access

KIND = "company_service_request"
ROLES = {
    "ownership_change": {"owner", "signer"},
    "settlement_adjustment": {"owner", "payer"},
}
TERMINAL = {"applied", "declined", "withdrawn", "expired", "resolved_unapplied"}


def authorize_request(item, user, kind):
    if kind not in ROLES:
        raise ValidationError({"kind": "Choose ownership or settlement correction."})
    access.require_role(item, user, ROLES[kind], sensitive=True)
    if kind == "ownership_change" and item.lease.status != "active":
        raise RentalConflict("Ownership continuation requires an active contract.")
    if (
        kind == "settlement_adjustment"
        and not FinalSettlement.objects.filter(
            lease=item.lease, execution_status="executed"
        ).exists()
    ):
        raise RentalConflict("A correction requires an executed original settlement.")
    if kind == "settlement_adjustment" and user.pk != item.lease.owner_id:
        access.require_delegate(item, user, "pay")


def request(item, user, data):
    from ..rental_lifecycle.cases import open_system_case

    kind = data["kind"]
    authorize_request(item, user, kind)
    # The caller holds the company/physical inventory/lease locks. Separate keys
    # and separate actors still discover the same unfinished service request.
    existing = (
        RentalOperationalCase.objects.select_for_update()
        .filter(lease=item.lease, kind=KIND, baseline__service_kind=kind)
        .exclude(status="resolved")
        .first()
    )
    if existing:
        # A distinct request joins the existing case, retaining its explanation.
        # The acknowledgement still advances the tenancy revision required by
        # the shared client receipt contract. Same-key replay never repeats this.
        audit(existing, user, "case.reply", data["reason"])
        existing.revision += 1
        existing.save()
        return access.changed(
            item,
            user,
            "company_service_joined",
            data["reason"],
            {"case_id": str(existing.id)},
        )
    case = open_system_case(
        kind=KIND,
        source_key=f"company-service:{item.id}:{kind}:{data['request_key']}",
        actor=user,
        lease=item.lease,
        reason=data["reason"],
        next_action="An independent operator will prepare the exact proposal. No ownership, consent or money has changed.",
    )
    case.team = "finance" if kind == "settlement_adjustment" else "support"
    case.baseline = {
        **case.baseline,
        "service_kind": kind,
        "tenancy_id": str(item.id),
    }
    case.save()
    return access.changed(item, user, "company_service_requested", data["reason"])


def tenancy(case):
    return get_object_or_404(CompanyTenancy, lease=case.lease)


def linked_change(case):
    identity = case.baseline.get("company_change_id")
    return (
        CompanyTenancyChange.objects.filter(
            id=identity, tenancy__lease=case.lease
        ).first()
        if identity
        else None
    )


def require_operator(case, user):
    from ..rental_lifecycle.cases import independent_case_operator

    require_actor(user)
    if user.sensitive_actions_frozen or not user.is_verified:
        raise PermissionDenied("Current verified operator access is required.")
    if (
        case.kind != KIND
        or case.status == "resolved"
        or case.assigned_to_id != user.pk
        or not independent_case_operator(case, user)
    ):
        raise PermissionDenied("The current assigned independent operator is required.")


def prepare(case, user, data):
    from ...company_tenancy_serializers import command_body
    from . import tenancy_ownership, tenancy_adjustments

    require_operator(case, user)
    if case.baseline.get("company_change_id"):
        raise RentalConflict("This request already has a canonical proposal.")
    item = tenancy(case)
    require_revision(item.lease, data.get("tenancy_revision"))
    # A removed requester cannot leave authority behind in a queue.
    authorize_request(item, case.opened_by, case.baseline["service_kind"])
    kind = case.baseline["service_kind"]
    body = command_body(
        kind,
        {
            **data.get("company_proposal", {}),
            "request_key": data["request_key"],
            "expected_revision": item.lease.revision,
            "reason": data["reason"],
        },
    )
    if kind == "ownership_change":
        if str(body["new_owner_id"]) == str(user.id):
            raise PermissionDenied(
                "The incoming owner cannot prepare their own transfer as operator."
            )
        tenancy_ownership.prepare(item, user, body)
        change_kind = "ownership"
    else:
        if str(body["financial_reviewer_id"]) == str(user.id):
            raise PermissionDenied(
                "A different financial reviewer must review the prepared proposal."
            )
        tenancy_adjustments.prepare(item, user, body)
        change_kind = "settlement_adjustment"
    change = item.changes.get(kind=change_kind, state="pending")
    case.baseline = {**case.baseline, "company_change_id": str(change.id)}
    case.status = "action_pending"
    case.next_action = "The named participants must review this exact proposal in their company tenancy. Operator preparation is not acceptance, signing or payment."
    audit(
        change,
        user,
        "company_service_prepared",
        data["reason"],
        {"case_id": str(case.id)},
    )


def requester_can_withdraw(item, change, user):
    return bool(
        access.roles(item, user) - access.PRIVATE_ONLY
        and RentalOperationalCase.objects.filter(
            kind=KIND,
            lease=item.lease,
            opened_by=user,
            baseline__company_change_id=str(change.id),
        ).exists()
    )


def withdraw(case, user):
    if case.kind != KIND or case.opened_by_id != user.pk or case.status == "resolved":
        raise PermissionDenied("Only the requester may withdraw an open request.")
    if case.baseline.get("company_change_id"):
        raise RentalConflict(
            "Review, decline or withdraw the canonical proposal from the tenancy."
        )
    authorize_request(tenancy(case), user, case.baseline["service_kind"])
    case.status = "resolved"
    case.resolution_code = "no_action_required"
    case.resolution = "Withdrawn by the requester before proposal preparation."
    case.next_action = "No proposal was created. Existing obligations remain unchanged."


def blocker(case):
    if case.kind != KIND:
        return ""
    change = linked_change(case)
    if case.baseline.get("company_change_id") and (
        not change or change.state not in TERMINAL
    ):
        return "Finish or safely withdraw the canonical proposal before closing this request."
    return ""


def validate_resolution(case, data):
    if case.kind != KIND:
        return
    change = linked_change(case)
    expected = (
        "corrected" if change and change.state == "applied" else "no_action_required"
    )
    if data.get("resolution_code") != expected:
        raise RentalConflict(f"The canonical outcome only supports {expected}.")


def projection(case, user):
    if case.kind != KIND:
        return None
    item = tenancy(case)
    change = linked_change(case)
    return {
        "tenancy_id": str(item.id),
        "kind": case.baseline["service_kind"],
        "proposal_id": str(change.id) if change else None,
        "proposal_state": change.state if change else None,
        "tenancy_revision": item.lease.revision,
        "can_open_tenancy": bool(access.roles(item, user)),
    }
