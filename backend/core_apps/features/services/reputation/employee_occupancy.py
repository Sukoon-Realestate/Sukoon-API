from django.conf import settings

"""Bilateral employee possession evidence, separate from planned assignments."""

from datetime import date
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound
from ...models import (
    EmployeeAssignment,
    EmployeeOccupancyConfirmation,
    CompanyMembership,
    CompanyLeaseBinding,
)
from .company_bindings import get as binding_for
from .company_authority import membership
from .policy import ReviewError, revision, require_actor
from .submission import command, audit
from . import ancestry


def binding(assignment):
    item = CompanyLeaseBinding.objects.filter(
        booking=assignment.item, state="accepted"
    ).first()
    if not item:
        raise ReviewError("experience_not_confirmed")
    return item


def coordinate(user, item):
    member = membership(user, item.renter_company)
    if not member.is_admin and (
        not member.is_coordinator or item.booking.request.coordinator_id != user.pk
    ):
        raise NotFound()


def fingerprint(assignment):
    return {
        "employee_id": str(assignment.employee.id),
        "property_id": str(assignment.property.id),
        "item_id": str(assignment.item.id),
        "space_key": assignment.space_key,
        "starts_on": assignment.starts_on.isoformat(),
        "ends_on": assignment.ends_on_exclusive.isoformat(),
    }


def confirmed(assignment):
    item = binding(assignment)
    rows = {
        x.kind: x
        for x in assignment.occupancy_confirmations.filter(
            state="accepted", accepted_at__isnull=False
        )
    }
    if set(rows) != {"arrival", "departure"}:
        raise ReviewError("occupancy_not_ended")
    start, end = rows["arrival"], rows["departure"]
    expected = fingerprint(assignment)
    if (
        start.source_snapshot.get("assignment") != expected
        or end.source_snapshot.get("assignment") != expected
        or end.possession_on < start.possession_on
        or end.accepted_at < start.accepted_at
        or any(not {"employee", "landlord"}.issubset(x.approvals) for x in (start, end))
    ):
        raise ReviewError("experience_not_confirmed")
    return item, start, end


def landlord_at(item, day):
    from .responsibility import transitions

    owner = item.lease.owner
    for change in transitions(item.lease):
        if change.effective_on <= day:
            owner = change.next_owner
    return owner


def landlord_confirmable(user, item, day):
    owner = landlord_at(item, day)
    if user.pk == owner.pk:
        return True
    if owner.pk == item.lease.owner_id and item.landlord_company_id:
        from .company_bindings import check_role

        try:
            check_role(user, item, "landlord_company")
            return True
        except (NotFound, ReviewError):
            pass
    return False


def read(user, assignment):
    require_actor(user)
    item = binding(assignment)
    from .responsibility import transitions

    owners = {
        item.lease.owner_id,
        *transitions(item.lease).values_list("next_owner_id", flat=True),
    }
    if user.pk not in owners | {assignment.employee_id}:
        if not (
            item.landlord_company_id
            and CompanyMembership.objects.filter(
                user=user, company=item.landlord_company, is_admin=True, is_active=True
            ).exists()
        ):
            coordinate(user, item)
    return item


def payload(assignment, user):
    item = read(user, assignment)
    rows = list(
        assignment.occupancy_confirmations.order_by("possession_on", "created_at")
    )
    roles = ["employee"] if user.pk == assignment.employee_id else ["landlord"]
    return {
        "id": str(assignment.id),
        "binding_id": str(item.id),
        "property_name": assignment.property.title,
        "employee_name": assignment.employee.get_full_name,
        "state": assignment.occupancy_status,
        "revision": assignment.revision,
        "starts_on": assignment.starts_on.isoformat(),
        "ends_on": assignment.ends_on_exclusive.isoformat(),
        "confirmations": [
            {
                "id": str(x.id),
                "kind": x.kind,
                "possession_on": x.possession_on.isoformat(),
                "state": x.state,
                "revision": x.revision,
                "confirmed_roles": list(x.approvals),
                "allowed_roles": (
                    [
                        r
                        for r in roles
                        if r not in x.approvals
                        and (
                            r == "employee"
                            or landlord_confirmable(user, item, x.possession_on)
                        )
                    ]
                    if x.state == "pending"
                    else []
                ),
            }
            for x in rows
        ],
    }


def assign(user, identity, body):
    item = binding_for(user, identity)
    from ..rental_lifecycle.locks import require_personal_workflow

    require_personal_workflow(item.lease)
    coordinate(user, item)

    def action():
        from .eligibility import lock_tenancy

        lock_tenancy(item.lease)
        locked = CompanyLeaseBinding.objects.select_for_update().get(pk=item.pk)
        coordinate(user, locked)
        if locked.state != "accepted" or not locked.booking_id:
            raise ReviewError("experience_not_confirmed")
        member = get_object_or_404(
            CompanyMembership,
            company=locked.renter_company,
            user__id=body.get("employee_id"),
            is_active=True,
            is_employee=True,
        )
        try:
            start, end = (
                date.fromisoformat(body.get(k, "")) for k in ("starts_on", "ends_on")
            )
        except (ValueError, TypeError):
            raise ReviewError("invalid_review_target", 400)
        # This binding proves only the canonical unit of its signed lease.
        if (
            not locked.lease.start_date <= start < end <= locked.lease.end_date
            or member.user_id in {locked.lease.owner_id, locked.lease.tenant_id}
        ):
            raise ReviewError("company_lease_mismatch")
        from ..company.assignment_locks import lock_people

        lock_people([member.user.id])
        if (
            EmployeeAssignment.objects.filter(
                employee=member.user, starts_on__lt=end, ends_on_exclusive__gt=start
            )
            .exclude(occupancy_status__in=["returned", "cancelled"])
            .exists()
        ):
            raise ReviewError("occupancy_overlap")
        assignment = EmployeeAssignment.objects.create(
            item=locked.booking,
            employee=member.user,
            property=locked.lease.property,
            starts_on=start,
            ends_on_exclusive=end,
        )
        audit(assignment, user, "employee_assignment_created")
        return payload(assignment, user)

    return command(user, f"review.assignment.{identity}", body, action, item.id)


def propose(user, identity, body):
    assignment = get_object_or_404(EmployeeAssignment, id=identity)
    item = read(user, assignment)
    from ..rental_lifecycle.locks import require_personal_workflow

    require_personal_workflow(item.lease)

    def action():
        from .eligibility import lock_tenancy

        lock_tenancy(item.lease)
        CompanyLeaseBinding.objects.select_for_update().get(pk=item.pk)
        locked = EmployeeAssignment.objects.select_for_update().get(pk=assignment.pk)
        read(user, locked)
        revision(locked, body.get("expected_revision"))
        kind = body.get("kind")
        try:
            day = date.fromisoformat(body.get("possession_on", ""))
        except (ValueError, TypeError):
            raise ReviewError("invalid_review_target", 400)
        if kind not in {"arrival", "departure"} or not locked.starts_on <= day <= min(
            timezone.localdate(), locked.ends_on_exclusive
        ):
            raise ReviewError("invalid_occupancy_date", 400)
        if locked.occupancy_confirmations.filter(kind=kind).exists():
            raise ReviewError("revision_conflict")
        if kind == "departure":
            arrival = locked.occupancy_confirmations.filter(
                kind="arrival", state="accepted"
            ).first()
            if not arrival or day < arrival.possession_on:
                raise ReviewError("experience_not_confirmed")
        snapshot = (
            ancestry.from_property(locked.property)
            if day == timezone.localdate()
            else ancestry.from_snapshot(
                item.source_snapshot.get("inventory_snapshot"), locked.property
            )
        )
        record = EmployeeOccupancyConfirmation.objects.create(
            assignment=locked,
            kind=kind,
            possession_on=day,
            proposed_by=user,
            assignment_revision=locked.revision,
            source_snapshot={
                "assignment": fingerprint(locked),
                "ancestry": snapshot,
                "landlord_id": str(landlord_at(item, day).id),
            },
        )
        audit(record, user, "employee_occupancy_proposed")
        return payload(locked, user)

    return command(
        user, f"review.occupancy.propose.{identity}", body, action, assignment.id
    )


def confirm(user, identity, body):
    record = get_object_or_404(EmployeeOccupancyConfirmation, id=identity)
    item = read(user, record.assignment)
    from ..rental_lifecycle.locks import require_personal_workflow

    require_personal_workflow(item.lease)
    role = body.get("role")

    def action():
        from .eligibility import lock_tenancy

        lock_tenancy(item.lease)
        CompanyLeaseBinding.objects.select_for_update().get(pk=item.pk)
        assignment = EmployeeAssignment.objects.select_for_update().get(
            pk=record.assignment_id
        )
        locked = EmployeeOccupancyConfirmation.objects.select_for_update().get(
            pk=record.pk
        )
        if (
            (role == "employee" and user.pk != assignment.employee_id)
            or (
                role == "landlord"
                and not landlord_confirmable(user, item, locked.possession_on)
            )
            or role not in {"employee", "landlord"}
        ):
            raise NotFound()
        if not user.is_verified:
            raise ReviewError("review_not_eligible", 403)
        revision(locked, body.get("expected_revision"))
        if (
            locked.state != "pending"
            or locked.source_snapshot["assignment"] != fingerprint(assignment)
            or locked.source_snapshot["landlord_id"]
            != str(landlord_at(item, locked.possession_on).id)
        ):
            raise ReviewError("revision_conflict")
        locked.approvals[role] = {
            "user_id": str(user.id),
            "at": timezone.now().isoformat(),
        }
        if {"employee", "landlord"}.issubset(locked.approvals):
            locked.state, locked.accepted_at = "accepted", timezone.now()
            assignment.occupancy_status = (
                "occupied" if locked.kind == "arrival" else "returned"
            )
            assignment.revision += 1
            assignment.save()
        locked.revision += 1
        locked.save()
        audit(locked, user, "employee_occupancy_confirmed")
        if (
            locked.state == "accepted"
            and locked.kind == "departure"
            and getattr(settings, "REVIEWS_ENABLED", False)
        ):
            from .company_generation import generate_employee

            generate_employee(assignment)
        return payload(assignment, user)

    return command(
        user, f"review.occupancy.confirm.{identity}", body, action, record.id
    )
