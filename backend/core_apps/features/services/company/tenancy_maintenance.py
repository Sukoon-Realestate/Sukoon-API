"""Canonical maintenance with unit-scoped resident access and company cost consent."""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from ...models import MaintenanceRequest, MaintenanceEvent, CompanyMaintenanceScope
from ..rental_phase2 import RentalConflict
from ..cycle_permissions import MAINTENANCE_TRANSITIONS
from . import tenancy_access as access


def occupants(item, prop):
    return item.preparation.booking.assignments.filter(
        property=prop, occupancy_status="occupied"
    )


def access_reviewers(item, scope):
    rows = list(occupants(item, scope.property).select_related("employee"))
    if rows:
        return {
            str(r.employee.id): {
                "version": scope.request.appointment_version,
                "assignment_id": str(r.id),
                "epoch": r.employee.security_epoch,
            }
            for r in rows
        }
    coordinator = item.coordinator
    return {
        str(coordinator.id): {
            "version": scope.request.appointment_version,
            "assignment_id": "",
            "epoch": coordinator.security_epoch,
        }
    }


def actions(item, scope, user):
    request, roles = scope.request, access.roles(item, user)
    resident = occupants(item, scope.property).filter(employee=user).exists()
    if not roles & {"owner", "coordinator", "payer"} and not resident:
        return []
    if request.status == "cancelled":
        return []
    available = {"reply"}
    if "owner" in roles:
        available |= {
            "acknowledge",
            "propose_appointment",
            "start_work",
            "report_resolved",
        }
        if request.status not in {"resolved", "resolution_reported"}:
            available.add("propose_cost")
    if resident or "coordinator" in roles:
        available |= {"confirm_resolved", "reopen", "report_missed"}
    if user.pk == request.reporter_id or "coordinator" in roles:
        available.add("cancel")
    if str(user.id) in access_reviewers(item, scope):
        available.add("revoke_access")
        if request.appointment_ends_at and timezone.now() < request.appointment_ends_at:
            available.add("accept_appointment")
    if request.proposed_cost_minor and (
        (request.cost_payer == "owner" and "owner" in roles)
        or (request.cost_payer == "company" and access.can_pay(item.lease, user))
    ):
        available |= {"approve_cost", "reject_cost"}
    return sorted(
        a
        for a in available
        if a not in MAINTENANCE_TRANSITIONS
        or request.status in MAINTENANCE_TRANSITIONS[a][0]
    )


def create(item, user, data):
    if (
        item.lease.status not in {"active", "termination_pending", "ended"}
        or item.lease.occupancy_status == "returned"
    ):
        raise RentalConflict(
            "Maintenance needs an existing serviceable company tenancy."
        )
    prop = next(
        (p for p in access.properties(item) if str(p.id) == str(data["property_id"])),
        None,
    )
    if prop is None:
        raise ValidationError("Choose a unit of this company contract.")
    if (
        not access.roles(item, user) & {"owner", "coordinator"}
        and not occupants(item, prop).filter(employee=user).exists()
    ):
        raise PermissionDenied(
            "Report maintenance only for your assigned occupied unit."
        )
    request = MaintenanceRequest.objects.create(
        lease=item.lease,
        reporter=user,
        title=data["title"],
        description=data["description"],
        category=data["category"],
        priority=data["priority"],
    )
    CompanyMaintenanceScope.objects.create(request=request, tenancy=item, property=prop)
    MaintenanceEvent.objects.create(
        maintenance_request=request, actor=user, action="created"
    )
    return access.changed(item, user, "company_maintenance_reported")


def act(item, user, data):
    scope = get_object_or_404(
        CompanyMaintenanceScope.objects.select_for_update(),
        tenancy=item,
        request__id=data["maintenance_id"],
    )
    request = MaintenanceRequest.objects.select_for_update().get(pk=scope.request_id)
    roles, action = access.roles(item, user), data["maintenance_action"]
    scope.request = request
    if action not in actions(item, scope, user):
        raise PermissionDenied(
            "This maintenance responsibility is not available in the current state."
        )
    resident = occupants(item, scope.property).filter(employee=user).exists()
    if not roles & {"owner", "coordinator", "payer"} and not resident:
        raise PermissionDenied("This maintenance request belongs to another unit.")
    if request.status == "cancelled":
        raise RentalConflict("This request is already cancelled.")
    owner_actions = {
        "acknowledge",
        "propose_appointment",
        "start_work",
        "report_resolved",
        "propose_cost",
    }
    if action in owner_actions and "owner" not in roles:
        raise PermissionDenied("Only the landlord may perform this maintenance action.")
    if (
        action in MAINTENANCE_TRANSITIONS
        and request.status not in MAINTENANCE_TRANSITIONS[action][0]
    ):
        raise RentalConflict("The maintenance state changed. Refresh before acting.")
    if action == "propose_appointment":
        start, end = data.get("appointment_at"), data.get("appointment_ends_at")
        if not start or not end or not timezone.now() < start < end:
            raise ValidationError("Choose a future bounded appointment.")
        request.appointment_at, request.appointment_ends_at = start, end
        request.appointment_version += 1
        request.access_approved_version = None
        scope.access_consents = {}
    elif action == "accept_appointment":
        if (
            str(user.id) not in access_reviewers(item, scope)
            or not request.appointment_ends_at
            or request.appointment_ends_at <= timezone.now()
        ):
            raise PermissionDenied(
                "Each current resident must approve their own access window."
            )
        access.require_role(item, user, access.roles(item, user), sensitive=True)
        needed = access_reviewers(item, scope)
        scope.access_consents[str(user.id)] = needed[str(user.id)]
        if not all(
            scope.access_consents.get(identity) == value
            for identity, value in needed.items()
        ):
            request.revision += 1
            request.save()
            scope.save()
            return access.changed(item, user, "company_maintenance_access_reviewed")
        request.access_approved_version = request.appointment_version
    elif action == "propose_cost":
        if data.get("cost_minor", 0) <= 0 or data.get("cost_payer") not in {
            "owner",
            "company",
        }:
            raise ValidationError(
                "Choose a positive cost and the owner or company as payer."
            )
        request.proposed_cost_minor = data["cost_minor"]
        request.cost_payer = data["cost_payer"]
        request.cost_version += 1
        request.approved_cost_version = None
        scope.cost_consent = {}
    elif action in {"approve_cost", "reject_cost"}:
        if request.cost_payer == "company":
            access.require_delegate(item, user, "pay")
        elif "owner" not in roles:
            raise PermissionDenied("Only the responsible payer may decide this cost.")
        if not request.proposed_cost_minor:
            raise RentalConflict("No cost is awaiting review.")
        request.approved_cost_version = (
            request.cost_version if action == "approve_cost" else None
        )
        scope.cost_consent = (
            {
                "payer_id": str(user.id),
                "security_epoch": user.security_epoch,
                "mandate_id": (
                    str(item.payer_mandate.id)
                    if request.cost_payer == "company"
                    else ""
                ),
                "mandate_revision": (
                    item.payer_mandate.revision
                    if request.cost_payer == "company"
                    else 0
                ),
            }
            if action == "approve_cost"
            else {}
        )
    elif action == "start_work":
        from ..maintenance_access import access_window_current

        needed = access_reviewers(item, scope)
        if (
            not access_window_current(request)
            or any(
                scope.access_consents.get(identity) != value
                for identity, value in needed.items()
            )
            or (
                request.proposed_cost_minor
                and request.approved_cost_version != request.cost_version
            )
        ):
            raise RentalConflict(
                "Current resident access and responsible-payer cost approval are required."
            )
        if request.proposed_cost_minor:
            payer = (
                item.payer_mandate.membership.user
                if request.cost_payer == "company"
                else item.lease.owner
            )
            if (
                scope.cost_consent.get("payer_id") != str(payer.id)
                or scope.cost_consent.get("security_epoch") != payer.security_epoch
                or not payer.is_active
                or payer.sensitive_actions_frozen
            ):
                raise RentalConflict(
                    "The payer authority changed. Review the cost again."
                )
            if request.cost_payer == "company":
                access.require_delegate(item, payer, "pay")
                if scope.cost_consent.get(
                    "mandate_revision"
                ) != item.payer_mandate.revision or scope.cost_consent.get(
                    "mandate_id"
                ) != str(
                    item.payer_mandate.id
                ):
                    raise RentalConflict(
                        "The payment mandate changed. Review the cost again."
                    )
    elif action == "confirm_resolved":
        if not resident and "coordinator" not in roles:
            raise PermissionDenied(
                "A resident or assigned coordinator must confirm resolution."
            )
    elif action == "report_missed":
        if (
            not request.appointment_ends_at
            or timezone.now() < request.appointment_ends_at
        ):
            raise RentalConflict("The appointment window has not ended.")
        request.access_approved_version = None
        scope.access_consents = {}
    elif action == "revoke_access":
        if str(user.id) not in access_reviewers(item, scope):
            raise PermissionDenied(
                "Only the resident may withdraw their own access consent."
            )
        scope.access_consents.pop(str(user.id), None)
        request.access_approved_version = None
        if request.status == "scheduled":
            request.status = "appointment_proposed"
    elif action not in set(MAINTENANCE_TRANSITIONS) | {"reply"}:
        raise ValidationError("Unsupported company maintenance action.")
    if action in MAINTENANCE_TRANSITIONS:
        request.status = MAINTENANCE_TRANSITIONS[action][1]
    request.revision += 1
    request.save()
    scope.save()
    MaintenanceEvent.objects.create(
        maintenance_request=request, actor=user, action=action, note=data["reason"]
    )
    return access.changed(item, user, "company_maintenance_" + action, data["reason"])
