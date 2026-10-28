"""Corporate possession and employee stays are distinct from the legal party."""

from datetime import date
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from ...models import (
    EmployeeAssignment,
    EmployeeOccupancyConfirmation,
    CompanyMembership,
    RentalHandover,
)
from ..rental_phase2 import RentalConflict
from . import tenancy_access as access, tenancy_changes as changes


def require_habitable(item, prop=None):
    from ..rental_lifecycle.habitability import assert_habitable

    for unit in [prop] if prop else access.properties(item):
        assert_habitable(unit, {"rental_scope": "entire_property"})


def propose_handover(item, user, data):
    access.require_role(item, user, {"owner", "coordinator"})
    kind = data["kind"]
    lease = item.lease
    if kind not in {"move_in", "move_out"} or lease.status not in {
        "active",
        "termination_pending",
        "ended",
    }:
        raise RentalConflict("A paid active or ending company tenancy is required.")
    if kind == "move_in" and (
        lease.status != "active" or lease.occupancy_status != "not_started"
    ):
        raise RentalConflict("Move-in requires an active unoccupied tenancy.")
    if kind == "move_in":
        require_habitable(item)
    returnable = {"occupied", "move_out_pending", "handover_disputed"}
    if lease.status == "ended":
        returnable.add(
            "not_started"
        )  # Bilateral confirmation of no possession still required.
    if kind == "move_out" and lease.occupancy_status not in returnable:
        raise RentalConflict("Confirm move-in before returning possession.")
    if not lease.start_date <= data["possession_on"] <= timezone.localdate():
        raise RentalConflict("Confirm an actual possession date, not a future event.")
    from ...rental_phase4_views_parts.handover_payload import _validate_evidence

    _validate_evidence(lease, data["evidence_ids"])
    content = {
        k: data[k] for k in ("condition", "keys", "meters", "inventory", "evidence_ids")
    }
    content["possession_on"] = str(data["possession_on"])
    content["evidence_ids"] = list(map(str, content["evidence_ids"]))
    roles = changes.current_roles(item)
    return changes.propose(
        item,
        user,
        kind,
        content,
        {k: roles[k] for k in ["owner", "coordinator"]},
        data["reason"],
    )


def apply_handover(item, change):
    data, lease = change.snapshot["content"], item.lease
    if change.kind == "move_in":
        require_habitable(item)
    if change.kind == "move_in" and (
        lease.status != "active" or lease.occupancy_status != "not_started"
    ):
        raise RentalConflict("Company move-in is no longer available.")
    returnable = {"occupied", "move_out_pending", "handover_disputed"}
    if lease.status == "ended":
        returnable.add("not_started")
    if change.kind == "move_out" and lease.occupancy_status not in returnable:
        raise RentalConflict("Company possession is no longer awaiting return.")
    if (
        change.kind == "move_out"
        and item.preparation.booking.assignments.exclude(
            occupancy_status__in=["returned", "cancelled", "arrival_pending"]
        ).exists()
    ):
        raise RentalConflict(
            "Confirm every employee departure before returning the company premises."
        )
    from ...rental_phase4_views_parts.handover_payload import _validate_evidence

    evidence = _validate_evidence(lease, data["evidence_ids"])
    if lease.handovers.filter(kind=change.kind).exists():
        raise RentalConflict("This company handover has already been recorded.")
    handover = RentalHandover.objects.create(
        lease=lease,
        kind=change.kind,
        status="accepted",
        possession_on=date.fromisoformat(data["possession_on"]),
        condition=data["condition"],
        keys=data["keys"],
        meters=data["meters"],
        inventory=data["inventory"],
        approvals=list(change.snapshot["required"].values()),
        accepted_at=timezone.now(),
        context_snapshot={
            "company_id": str(lease.renter_company.id),
            "owner_id": str(lease.owner.id),
            "inventory": item.source_snapshot["inventory"],
            "source_change_id": str(change.id),
        },
    )
    handover.evidence.set(evidence)
    lease.occupancy_status = "occupied" if change.kind == "move_in" else "returned"
    if change.kind == "move_out":
        # Physical return is explicit, not inferred from employment or the legal end.
        lease.inventory_day_locks.filter(kind="occupied").delete()
        item.preparation.booking.assignments.filter(
            occupancy_status="arrival_pending"
        ).update(occupancy_status="cancelled")
    from ...rental_phase4_views_parts.handover_respond import evaluate_owner_payables

    evaluate_owner_payables(lease)


def assignment(item, identity):
    return get_object_or_404(
        EmployeeAssignment.objects.select_for_update(),
        item=item.preparation.booking,
        id=identity,
    )


def propose_presence(item, user, data):
    access.require_role(item, user, {"owner", "employee"}, sensitive=True)
    row = assignment(item, data["assignment_id"])
    if user.pk not in {row.employee_id, item.lease.owner_id}:
        raise PermissionDenied(
            "The employee or landlord must record actual employee possession."
        )
    kind, day = data["kind"], data["possession_on"]
    if (
        kind not in {"arrival", "departure"}
        or not row.starts_on <= day <= timezone.localdate()
    ):
        raise RentalConflict(
            "Choose a valid actual employee arrival or departure date."
        )
    if kind == "arrival":
        require_habitable(item, row.property)
        if (
            item.lease.status != "active"
            or item.lease.occupancy_status != "occupied"
            or row.occupancy_status != "arrival_pending"
            or day >= row.ends_on_exclusive
        ):
            raise RentalConflict(
                "Accept company move-in and the current assignment before employee arrival."
            )
        if not CompanyMembership.objects.filter(
            company=item.lease.renter_company,
            user=row.employee,
            is_active=True,
            is_employee=True,
        ).exists():
            raise RentalConflict(
                "The arriving employee no longer has active company membership."
            )
    elif row.occupancy_status != "occupied":
        raise RentalConflict(
            "A confirmed arrival is required before employee departure."
        )
    from ..reputation.employee_occupancy import fingerprint
    from ..reputation.ancestry import from_property

    existing = row.occupancy_confirmations.filter(kind=kind).first()
    if existing and existing.state not in {"disputed", "cancelled"}:
        raise RentalConflict("Review the existing employee possession confirmation.")
    if kind == "departure":
        arrival = row.occupancy_confirmations.get(kind="arrival", state="accepted")
        if day < arrival.possession_on:
            raise RentalConflict("Departure cannot precede actual arrival.")
    source = {
        "assignment": fingerprint(row),
        "ancestry": from_property(row.property),
        "landlord_id": str(item.lease.owner.id),
    }
    if existing:
        from ..rental_lifecycle.common import audit

        audit(
            existing,
            user,
            "company_possession_corrected",
            data["reason"],
            {
                "previous_date": str(existing.possession_on),
                "previous_snapshot": existing.source_snapshot,
                "previous_approvals": existing.approvals,
            },
        )
        existing.possession_on, existing.proposed_by = day, user
        existing.source_snapshot, existing.approvals, existing.state = (
            source,
            {},
            "pending",
        )
        existing.assignment_revision = row.revision
        existing.revision += 1
        existing.save()
    else:
        EmployeeOccupancyConfirmation.objects.create(
            assignment=row,
            kind=kind,
            possession_on=day,
            proposed_by=user,
            assignment_revision=row.revision,
            source_snapshot=source,
        )
    return access.changed(
        item,
        user,
        "company_employee_possession_proposed",
        metadata={"assignment_id": str(row.id)},
    )


def confirm_presence(item, user, data):
    access.require_role(
        item, user, {data["role"]}, sensitive=data["decision"] == "accept"
    )
    record = get_object_or_404(
        EmployeeOccupancyConfirmation.objects.select_for_update(),
        id=data["confirmation_id"],
        assignment__item=item.preparation.booking,
    )
    row = assignment(item, record.assignment.id)
    role = data["role"]
    if (
        (role == "employee" and user.pk != row.employee_id)
        or (role == "owner" and user.pk != item.lease.owner_id)
        or role not in {"employee", "owner"}
    ):
        raise PermissionDenied(
            "Each participant must confirm their own possession responsibility."
        )
    if record.state != "pending":
        raise RentalConflict("This possession confirmation is already closed.")
    from ..reputation.employee_occupancy import fingerprint

    if record.source_snapshot["assignment"] != fingerprint(row):
        raise RentalConflict("The employee assignment changed.")
    if data["decision"] == "decline":
        record.state = "disputed"
    elif data["decision"] == "accept":
        if record.kind == "arrival":
            require_habitable(item, row.property)
        if record.kind == "arrival" and (
            item.lease.status != "active"
            or not CompanyMembership.objects.filter(
                company=item.lease.renter_company,
                user=row.employee,
                is_active=True,
                is_employee=True,
                user__is_active=True,
                user__is_verified=True,
                user__sensitive_actions_frozen=False,
            ).exists()
        ):
            raise RentalConflict(
                "The arriving employee no longer has current company authority."
            )
        mapped = "landlord" if role == "owner" else role
        record.approvals[mapped] = {
            "user_id": str(user.id),
            "at": timezone.now().isoformat(),
        }
        if {"employee", "landlord"}.issubset(record.approvals):
            if record.kind == "arrival" and (
                row.occupancy_status != "arrival_pending"
                or item.lease.occupancy_status != "occupied"
            ):
                raise RentalConflict("This employee arrival is no longer available.")
            if record.kind == "departure" and row.occupancy_status != "occupied":
                raise RentalConflict(
                    "The employee is not recorded as occupying this assignment."
                )
            record.state, record.accepted_at = "accepted", timezone.now()
            row.occupancy_status = (
                "occupied" if record.kind == "arrival" else "returned"
            )
            row.revision += 1
            row.save()
    else:
        raise RentalConflict("Choose accept or decline.")
    record.revision += 1
    record.save()
    return access.changed(
        item,
        user,
        "company_employee_possession_decided",
        data["reason"],
        metadata={"assignment_id": str(row.id)},
    )


def propose_replacement(item, user, data):
    access.require_role(item, user, {"coordinator"}, sensitive=True)
    if item.lease.status != "active":
        raise RentalConflict("Employee replacement requires an active company tenancy.")
    previous = assignment(item, data["assignment_id"])
    if item.changes.filter(
        kind="replacement",
        state="applied",
        snapshot__content__assignment_id=str(previous.id),
    ).exists():
        raise RentalConflict(
            "This assignment was already replaced. Select the current assignment."
        )
    if previous.occupancy_status not in {"occupied", "arrival_pending", "returned"}:
        raise RentalConflict("This assignment cannot be replaced.")
    incoming = get_object_or_404(
        CompanyMembership,
        company=item.lease.renter_company,
        user__id=data["employee_id"],
        is_active=True,
        is_employee=True,
        user__is_active=True,
        user__is_verified=True,
    )
    if incoming.user_id in {previous.employee_id, item.lease.owner_id}:
        raise RentalConflict("Choose a different eligible company employee.")
    if (
        not max(timezone.localdate(), item.lease.start_date)
        <= data["effective_on"]
        < item.lease.end_date
    ):
        raise RentalConflict(
            "Choose a current or future date within the existing company tenancy."
        )
    required = changes.current_roles(item)
    required = {k: required[k] for k in ["owner", "coordinator"]}
    required["incoming_employee"] = str(incoming.user.id)
    required["outgoing_employee"] = str(previous.employee.id)
    return changes.propose(
        item,
        user,
        "replacement",
        {
            "assignment_id": str(previous.id),
            "assignment_revision": previous.revision,
            "employee_id": str(incoming.user.id),
            "membership_id": str(incoming.id),
            "membership_revision": incoming.revision,
            "property_id": str(previous.property.id),
            "employee_name": incoming.user.get_full_name,
            "property_name": previous.property.title,
            "effective_on": str(data["effective_on"]),
        },
        required,
        data["reason"],
    )


def apply_replacement(item, change):
    body = change.snapshot["content"]
    previous = assignment(item, body["assignment_id"])
    if item.changes.filter(
        kind="replacement",
        state="applied",
        snapshot__content__assignment_id=str(previous.id),
    ).exists():
        raise RentalConflict("This assignment was already replaced.")
    if previous.occupancy_status == "occupied":
        return False
    if previous.occupancy_status not in {"arrival_pending", "returned"}:
        raise RentalConflict("The outgoing assignment is no longer replaceable.")
    membership = get_object_or_404(
        CompanyMembership,
        id=body["membership_id"],
        revision=body["membership_revision"],
        is_active=True,
        is_employee=True,
    )
    start = date.fromisoformat(body["effective_on"])
    if start < timezone.localdate() or item.lease.status != "active":
        raise RentalConflict(
            "The proposed replacement date has passed; withdraw and review a new date."
        )
    from .assignment_locks import lock_people, require_available

    lock_people([membership.user.id])
    require_available(membership.user, start, item.lease.end_date)
    if previous.occupancy_status == "arrival_pending":
        previous.occupancy_status = "cancelled"
        previous.revision += 1
        previous.save()
    EmployeeAssignment.objects.create(
        item=previous.item,
        employee=membership.user,
        property=previous.property,
        starts_on=start,
        ends_on_exclusive=item.lease.end_date,
        acknowledgment="accepted",
        acknowledged_revision=1,
    )
    return True
