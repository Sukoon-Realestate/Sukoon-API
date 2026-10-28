"""Administrative succession over canonical assignments, without rental disclosure."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from ...models import CompanyTenancy, CompanyTenancyChange, CompanyMembership
from .access import company_for
from . import tenancy_access as access, tenancy_changes as changes, tenancy_closure
from .role_context import system_context
from ..rental_lifecycle.common import require_revision


def get(user, company_id, identity, *, lock=False):
    company = company_for(user, company_id, "admin", lock=lock)
    item = get_object_or_404(CompanyTenancy, id=identity, lease__renter_company=company)
    if lock:
        lease = access.lock_lease(item.lease)
        item = CompanyTenancy.objects.select_for_update().get(pk=item.pk)
        item.lease = lease
    return item


def payload(item, user, *, choices=False):
    company = item.lease.renter_company
    company_for(user, company.id, "admin")
    pending = item.changes.filter(kind="authority", state="pending").order_by(
        "created_at"
    )
    value = {
        "id": str(item.id),
        "company_id": str(company.id),
        "revision": item.revision,
        "title": item.preparation.booking.request.title,
        "coordinator_name": item.coordinator.get_full_name,
        "signer_name": item.signer_mandate.membership.user.get_full_name,
        "payer_name": item.payer_mandate.membership.user.get_full_name,
        "can_propose": not pending.exists()
        and item.lease.status
        in {"signed", "active", "termination_pending", "ended", "cancelled"},
        "changes": [
            {
                "id": str(change.id),
                "revision": change.revision,
                "digest": change.snapshot_digest,
                "state": change.state,
                "reason": change.reason,
                "signer_name": change.snapshot["content"]["signer_name"],
                "payer_name": change.snapshot["content"]["payer_name"],
                "coordinator_name": change.snapshot["content"]["coordinator_name"],
                "reviewer_name": change.snapshot["content"]["reviewer_name"],
                "can_decide": change.snapshot["required"].get("administrator")
                == str(user.id)
                and "administrator" not in change.decisions,
            }
            for change in pending
        ],
    }
    if choices:
        people = CompanyMembership.objects.filter(
            company=company,
            is_active=True,
            user__is_active=True,
            user__is_verified=True,
        ).select_related("user")
        for key, flag in (
            ("coordinators", "is_coordinator"),
            ("reviewers", "is_admin"),
        ):
            value[key] = [
                {"id": str(member.id), "name": member.user.get_full_name}
                for member in people
                if getattr(member, flag)
                and member.user_id != item.lease.owner_id
                and (key != "reviewers" or member.user_id != user.pk)
            ]
        for kind, key in (("sign", "signers"), ("pay", "payers")):
            value[key] = [
                {"id": str(m.id), "name": m.membership.user.get_full_name}
                for m in company.mandates.filter(
                    kind=kind, state="approved"
                ).select_related("membership__user")
                if access.execution_mandate(m)
                and m.membership.user_id != item.lease.owner_id
            ]
    return value


def authorize_decision(item, user, data):
    change = get_object_or_404(
        CompanyTenancyChange, tenancy=item, id=data["change_id"], kind="authority"
    )
    if data.get("role") != "administrator" or change.snapshot["required"].get(
        "administrator"
    ) != str(user.id):
        raise PermissionDenied(
            "Only the named independent administrator may review succession."
        )
    return change


def execute(item, user, action, data):
    require_revision(item.lease, data["expected_revision"])
    # The admin company/resource check above is mandatory. The existing domain
    # command still verifies independent identities and current execution grants;
    # it is not allowed to inherit a contract or payment HTTP projection.
    with system_context():
        if action == "replace_authority":
            return tenancy_closure.propose_authority(item, user, data)
        authorize_decision(item, user, data)
        return changes.respond(item, user, data)


def recovery_subject(user, identity, operation=None):
    """Authorize receipt metadata only, never a general tenancy subject grant."""
    from .role_context import http_context
    from ...models import CompanyHousingRequest, CompanyBookingItem

    request = http_context(user)
    if request is None or request.headers.get("X-Sukoon-Company-Role") != "admin":
        return None
    kinds = {
        CompanyTenancy: {
            "company.responsibility.replace_authority",
            "company.responsibility.respond_change",
        },
        CompanyHousingRequest: {"company.coordinator.reassign"},
        CompanyBookingItem: {"company.approval.reassign"},
    }
    for model, operations in kinds.items():
        if operation is not None and operation.operation not in operations:
            continue
        item = model.objects.filter(id=identity).first()
        if item is None:
            continue
        company = (
            item.lease.renter_company
            if isinstance(item, CompanyTenancy)
            else (
                item.company
                if isinstance(item, CompanyHousingRequest)
                else item.request.company
            )
        )
        company_for(user, company.id, "admin")
        return item
    return None


def notify(item, change, user):
    from .role_notifications import record

    if str(user.id) not in {
        str(change.proposed_by.id),
        change.snapshot["required"].get("administrator"),
    }:
        return
    record(
        user=user,
        company=item.lease.renter_company,
        role="admin",
        key=f"company.responsibility:{item.id}:{item.revision}",
        destination={
            "action_type": "open_company_responsibility",
            "target_id": str(item.id),
            "workspace": "company",
            "schema_version": "1",
            "event_kind": "company_responsibility_updated",
        },
    )
