"""Recipient-scoped corporate updates; historical notices open the current tenancy."""

from rest_framework.exceptions import NotFound
from ...planning_models import PlanningEvent
from . import tenancy_access as access


def workspace(item, user):
    roles = access.roles(item, user)
    if not roles:
        return None
    return "owner" if roles & {"owner", "new_owner"} else "company"


def event_roles(item, user, action, metadata):
    """Only participants of this task receive its activity or badge."""
    from .role_context import resource_role

    if metadata.get("change_id"):
        change = item.changes.get(id=metadata["change_id"])
        prior_owner = access.prior_owner_roles(item, change, user)
        return {
            (
                "owner"
                if role in {"owner", "new_owner"} or role in prior_owner
                else resource_role(role)
            )
            for role, identity in change.snapshot["required"].items()
            if identity == str(user.id)
        }
    if metadata.get("assignment_id"):
        assignment = item.preparation.booking.assignments.get(
            id=metadata["assignment_id"]
        )
        return {"owner", "coordinator"} | (
            {"employee"} if assignment.employee_id == user.pk else set()
        )
    if metadata.get("maintenance_id"):
        scope = item.maintenance_scopes.select_related("request").get(
            request__id=metadata["maintenance_id"]
        )
        if action.endswith(("propose_cost", "approve_cost", "reject_cost")):
            return {"owner", "payer"}
        resident = item.preparation.booking.assignments.filter(
            property=scope.property, employee=user, occupancy_status="occupied"
        ).exists()
        own_or_access = scope.request.reporter_id == user.pk or bool(
            scope.request.appointment_at
        )
        return {"owner", "coordinator"} | (
            {"employee"} if resident and own_or_access else set()
        )
    if action == "company_agreement_signed":
        return {"owner", "signer", "payer"}
    if any(
        part in action for part in ("signature", "signing", "agreement", "continuation")
    ):
        return {"owner", "signer"}
    if action in {"company_tenancy_updated", "company_tenancy_reconciled"}:
        return {"owner", "coordinator", "signer"} | (
            {"payer"} if item.lease.status in {"signed", "active", "ended"} else set()
        )
    # Unknown legacy event kinds have no verified company audience.
    return {"owner"}


def record(item, people, action, actor=None, metadata=None):
    from core_apps.users.models import User
    from .role_context import system_context, resource_role
    from .role_notifications import record as notify

    with system_context():
        change = item.changes.filter(id=(metadata or {}).get("change_id")).first()
        for user in User.objects.filter(pk__in=people, is_active=True):
            if change and change.kind == "authority":
                from .responsibility_management import notify as notify_management

                notify_management(item, change, user)
            responsibilities = access.roles(item, user)
            prior_owner = "prior_signer" in responsibilities and any(
                access.prior_owner_roles(item, change, user)
                for change in item.changes.filter(
                    kind="continuation_release", state__in=access.OPEN_REVIEW
                )
            )
            if responsibilities & {"owner", "new_owner"} or prior_owner:
                audiences = {"owner"}
            else:
                audiences = {
                    resource_role(r)
                    for r in responsibilities
                    if resource_role(r) and r != "administrator"
                }
            audiences &= event_roles(item, user, action, metadata or {})
            for role in audiences:
                notify(
                    user=user,
                    company=item.lease.renter_company,
                    role=role,
                    key=f"company.tenancy:{item.id}:{item.revision}",
                    destination={
                        "action_type": "open_company_tenancy",
                        "target_id": str(item.id),
                        "lease_id": str(item.lease.id),
                        "workspace": "owner" if role == "owner" else "company",
                        "schema_version": "1",
                        "revision": item.revision,
                        "event_kind": "company_tenancy_updated",
                        "change_kind": action,
                        # Other actors' identities do not belong to this role's
                        # activity feed; the resource gives its own task detail.
                        "actor_id": (
                            str(actor.id) if actor and actor.pk == user.pk else ""
                        ),
                    },
                )


def authorize(event):
    item = access.get(event.recipient, event.destination["target_id"])
    data = event.destination
    # Preserve already-queued legacy notices; all new events carry explicit binding.
    if data.get("event_kind") == "company_tenancy_updated" and (
        data.get("company_id") != str(item.lease.renter_company.id)
        or data.get("lease_id") != str(item.lease.id)
        or data.get("workspace") != workspace(item, event.recipient)
    ):
        raise NotFound()
    return {
        "title": "تحديث سكن الشركة / Company tenancy updated",
        "body": "راجع الحالة الحالية والمهمة المتاحة لك وسجل التغيير. / Review the current state, your task and its history.",
    }


def history(item, user):
    return [
        {
            "revision": event.destination.get("revision", 0),
            "company_role": event.destination.get("company_role", ""),
            "actor_id": event.destination.get("actor_id", ""),
            "action": event.destination.get("change_kind", "company_tenancy_updated"),
            "occurred_at": event.created_at.isoformat(),
        }
        for event in PlanningEvent.objects.filter(
            recipient=user,
            destination__target_id=str(item.id),
            destination__event_kind="company_tenancy_updated",
        ).order_by("created_at", "pk")
    ]
