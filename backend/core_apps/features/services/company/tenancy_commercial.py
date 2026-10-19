"""Exact corporate continuations; future obligations never rewrite issued invoices."""

from copy import deepcopy
from datetime import date, timedelta, time
from django.db.models import Sum, Max
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from ...models import (
    CompanyMembership,
    CompanyBudgetReservation,
    CompanyTenancyChange,
    RentalChange,
    BillingPeriod,
    EmployeeAssignment,
)
from ..rental_phase2 import RentalConflict, fingerprint, add_months
from ..rental_phase3_parts.issue_invoice import cairo_instant
from . import tenancy_access as access, tenancy_changes as changes

KINDS = {"renewal", "amendment", "ownership"}
OPEN = {"pending", "accepted", "pending_signatures", "review_required"}


def assert_no_continuation(item):
    if item.changes.filter(kind__in=KINDS, state__in=OPEN).exists():
        raise RentalConflict(
            "Resolve or withdraw the existing contract continuation first.",
            code="continuation_open",
        )


def budget(item):
    return CompanyBudgetReservation.objects.select_for_update().get(
        item=item.preparation.booking
    )


def exposure(item):
    row = CompanyBudgetReservation.objects.filter(item=item.preparation.booking).first()
    base = (
        (row.rent_minor + row.deposit_minor)
        if row
        else (
            item.source_snapshot["full_term_rent_minor"]
            + item.source_snapshot["deposit_minor"]
        )
    )
    # Additive corrections are separate from rental-budget periods, but still
    # form part of the actual representative's financial authority exposure.
    corrections = sum(
        max(0, invoice.charges_minor - invoice.credits_minor)
        for invoice in item.lease.invoices.filter(invoice_type="adjustment").exclude(
            status__in=["cancelled", "written_off"]
        )
    )
    return base + corrections


def approver(item, identity, proposer):
    row = CompanyMembership.objects.filter(
        company=item.lease.renter_company,
        id=identity,
        is_active=True,
        is_approver=True,
        user__is_active=True,
        user__is_verified=True,
    ).first()
    excluded = {
        item.lease.owner_id,
        item.coordinator_id,
        proposer.pk,
        item.signer_mandate.membership.user_id,
        item.payer_mandate.membership.user_id,
    }
    if (
        not row
        or row.user_id in excluded
        or item.preparation.booking.assignments.filter(employee=row.user).exists()
    ):
        raise PermissionDenied(
            "Choose a current company approver independent of the parties, coordinator and residents."
        )
    return row


def periods(item):
    return [
        {
            "id": str(p.id),
            "start": str(p.start),
            "end": str(p.end_exclusive),
            "amount": p.amount_minor,
            "status": p.status,
        }
        for p in item.lease.billing_periods.order_by("sequence")
    ]


def roster(item):
    return [
        {
            "id": str(a.id),
            "revision": a.revision,
            "employee_id": str(a.employee.id),
            "property_id": str(a.property.id),
            "ends_on_exclusive": str(a.ends_on_exclusive),
        }
        for a in item.preparation.booking.assignments.select_related(
            "employee", "property"
        )
        .exclude(occupancy_status__in=["returned", "cancelled"])
        .order_by("id")
    ]


def propose(item, user, data):
    access.require_role(item, user, {"owner", "signer"}, sensitive=True)
    if user.pk != item.lease.owner_id:
        access.require_delegate(item, user, "sign")
    assert_no_continuation(item)
    if item.lease.status != "active":
        raise RentalConflict(
            "Only an active company tenancy supports commercial continuation."
        )
    kind = data["kind"]
    if kind not in {"renewal", "amendment"}:
        raise RentalConflict("Choose renewal or amendment.")
    reviewer = approver(item, data["reviewer_membership_id"], user)
    start, end = data["effective_on"], data["ends_on_exclusive"]
    if start < timezone.localdate() or end <= start or (end - start).days > 3660:
        raise RentalConflict("Choose a current or future supported term.")
    rent = data["rent_minor"]
    months = next((n for n in range(1, 121) if add_months(start, n) == end), None)
    if not months:
        raise RentalConflict(
            "Only complete calendar billing months are supported; proration is not approved."
        )
    if kind == "renewal" and start != item.lease.end_date:
        raise RentalConflict("Renewal must start exactly at the current exclusive end.")
    affected = list(
        item.lease.billing_periods.filter(start__gte=start).order_by("sequence")
    )
    if kind == "amendment" and (
        end != item.lease.end_date
        or not affected
        or affected[0].start != start
        or any(p.status != "scheduled" or hasattr(p, "invoice") for p in affected)
    ):
        raise RentalConflict(
            "Amend only complete, unissued future billing periods. Issued obligations require settlement correction."
        )
    rows = roster(item)
    terms = deepcopy(item.lease.terms)
    terms.update(
        starts_on=str(start),
        ends_on_exclusive=str(end),
        rent={"amount_minor": rent, "currency": "EGP", "exponent": 2},
        signer_id=str(item.signer_mandate.membership.user.id),
        owner_id=str(item.lease.owner.id),
        billing_anchor_day=start.day,
        continuation_kind=kind,
        previous_terms_digest=item.terms_digest,
        employee_placements=rows,
        renewal_commission_basis_points=0,
    )
    delta = rent * months - (
        sum(p.amount_minor for p in affected) if kind == "amendment" else 0
    )
    content = {
        "effective_on": str(start),
        "ends_on_exclusive": str(end),
        "terms": terms,
        "months": months,
        "rent_delta_minor": delta,
        "roster": rows,
        "periods": periods(item),
        "reviewer_membership_id": str(reviewer.id),
        "reviewer_revision": reviewer.revision,
    }
    roles = changes.current_roles(item)
    required = {k: roles[k] for k in ["owner", "signer", "payer"]}
    required["approver"] = str(reviewer.user.id)
    if kind == "renewal":
        required.update(
            {"resident_" + str(i): r["employee_id"] for i, r in enumerate(rows)}
        )
    changes.propose(item, user, kind, content, required, data["reason"])
    change = item.changes.get(kind=kind, state="pending")
    change.rental_change = RentalChange.objects.create(
        lease=item.lease,
        requester=user,
        kind=kind,
        terms=terms,
        previous_terms=deepcopy(item.lease.terms),
        effective_on=start,
        reason=data["reason"],
    )
    change.save()
    return item


def revalidate(item, change):
    body = change.snapshot["content"]
    if (
        change.snapshot["terms_digest"] != item.terms_digest
        or item.lease.status != "active"
    ):
        raise RentalConflict(
            "The underlying contract changed; a fresh review is required."
        )
    if change.kind == "ownership":
        from .tenancy_ownership import validate

        validate(item, change)
        return
    if roster(item) != body["roster"]:
        raise RentalConflict(
            "Employee placements changed; obtain fresh independent reviews."
        )
    if date.fromisoformat(body["effective_on"]) < timezone.localdate():
        raise RentalConflict(
            "The agreed effective date passed; reconcile before committing the change."
        )
    if change.kind == "amendment" and periods(item) != body["periods"]:
        raise RentalConflict(
            "Billing changed after review; issued obligations cannot be rewritten."
        )
    approver(item, body["reviewer_membership_id"], change.proposed_by)
    if (
        change.kind == "amendment"
        and len([p for p in body["periods"] if p["start"] >= body["effective_on"]])
        != body["months"]
    ):
        raise RentalConflict(
            "The proposed months do not match the canonical billing periods."
        )
    if change.kind == "renewal":
        from .assignment_locks import lock_people

        lock_people(r["employee_id"] for r in body["roster"])
        for r in body["roster"]:
            if (
                EmployeeAssignment.objects.filter(
                    employee__id=r["employee_id"],
                    starts_on__lt=body["ends_on_exclusive"],
                    ends_on_exclusive__gt=body["effective_on"],
                )
                .exclude(id=r["id"])
                .exclude(occupancy_status__in=["returned", "cancelled"])
                .exists()
            ):
                raise RentalConflict("An employee has a conflicting future placement.")
        from ..rental_lifecycle.inventory import assert_available

        for prop in access.properties(item, lock=True):
            if prop.owner_id != item.lease.owner_id or not prop.is_ownership_verified:
                raise RentalConflict(
                    "Review current ownership of every included property."
                )
            assert_available(
                prop,
                {"rental_scope": "entire_property"},
                date.fromisoformat(body["effective_on"]),
                date.fromisoformat(body["ends_on_exclusive"]),
                exclude_lease=item.lease,
            )


def reserve(item, change):
    revalidate(item, change)
    if change.kind == "ownership":
        change.rental_change.status = "accepted"
        change.rental_change.save()
        return
    current = budget(item)
    increment = max(0, change.snapshot["content"]["rent_delta_minor"])
    company = item.lease.renter_company
    from .bookings import _live_reservations

    rows = _live_reservations(company)
    for selected, limit in [
        (rows, company.budget_limit_minor),
        (
            rows.filter(item__request=item.preparation.booking.request),
            item.preparation.booking.request.commitment_ceiling_minor,
        ),
    ]:
        if (
            limit is not None
            and (selected.aggregate(total=Sum("rent_minor"))["total"] or 0) + increment
            > limit
        ):
            raise RentalConflict(
                "The continuation exceeds the current approved budget.",
                code="budget_exceeded",
            )
    for mandate in [item.signer_mandate, item.payer_mandate]:
        if not access.execution_mandate(mandate, exposure=exposure(item) + increment):
            raise RentalConflict(
                "Renew verified signing and payment authority for the full exposure."
            )
    current.rent_minor += increment
    current.save()
    change.reserved_rent_minor = increment
    change.save()
    if change.kind == "renewal":
        from ..rental_lifecycle.inventory import allocate_days

        body = change.snapshot["content"]
        for prop in access.properties(item, lock=True):
            rows = allocate_days(
                prop=prop,
                snapshot={"rental_scope": "entire_property"},
                offer_id=item.lease.offer_id,
                starts_on=date.fromisoformat(body["effective_on"]),
                ends_on=date.fromisoformat(body["ends_on_exclusive"]),
                expires_at=None,
                lease=item.lease,
            )
            # Approved, unsigned continuation is protected independently of the
            # original occupied days; no expiry can release an unknown signature.
            for row in rows:
                row.company_change = change
                row.kind = "hold"
            from ...models import RentalInventoryDayLock

            RentalInventoryDayLock.objects.bulk_update(rows, ["company_change", "kind"])
    change.rental_change.status = "accepted"
    change.rental_change.save()


def release(item, change):
    if change.rental_change_id and change.rental_change.signing_sessions.exists():
        raise RentalConflict(
            "Reconcile the original signing session before any release; its outcome may be unknown."
        )
    if change.reserved_rent_minor:
        row = budget(item)
        row.rent_minor -= change.reserved_rent_minor
        row.save()
        change.reserved_rent_minor = 0
    change.inventory_locks.filter(kind="hold").delete()
    if change.rental_change_id:
        change.rental_change.status = "rejected"
        change.rental_change.revision += 1
        change.rental_change.save()
    change.save()


def apply_signed(item, change):
    revalidate(item, change)
    event = change.rental_change
    if event.status != "signed" or not event.document_hash or not event.document_id:
        raise RentalConflict(
            "Authoritative signatures for the exact continuation are required."
        )
    if change.kind == "ownership":
        from .tenancy_ownership import apply

        apply(item, change)
    else:
        body = change.snapshot["content"]
        rent = body["terms"]["rent"]["amount_minor"]
        if change.kind == "renewal":
            start = date.fromisoformat(body["effective_on"])
            sequence = item.lease.billing_periods.aggregate(n=Max("sequence"))["n"] or 0
            for n in range(body["months"]):
                day, end = add_months(start, n), add_months(start, n + 1)
                BillingPeriod.objects.create(
                    lease=item.lease,
                    sequence=sequence + n + 1,
                    start=day,
                    end_exclusive=end,
                    issue_at=cairo_instant(day) - timedelta(days=7),
                    due_at=cairo_instant(day, time.max),
                    amount_minor=rent,
                )
            for row in body["roster"]:
                assignment = EmployeeAssignment.objects.get(id=row["id"])
                assignment.ends_on_exclusive = date.fromisoformat(
                    body["ends_on_exclusive"]
                )
                assignment.revision += 1
                assignment.acknowledged_revision = assignment.revision
                assignment.save()
            change.inventory_locks.update(kind="occupied", expires_at=None)
            item.lease.end_date = date.fromisoformat(body["ends_on_exclusive"])
        else:
            item.lease.billing_periods.filter(start__gte=body["effective_on"]).update(
                amount_minor=rent
            )
            if body["rent_delta_minor"] < 0:
                row = budget(item)
                row.rent_minor += body["rent_delta_minor"]
                row.save()
        item.lease.rent_amount_minor = rent
        item.lease.terms = deepcopy(body["terms"])
    item.lease.document_id, item.lease.document_hash = (
        event.document_id,
        event.document_hash,
    )
    item.terms_digest = fingerprint(item.lease.terms)
    item.save()
    item.lease.save()
    change.state, change.applied_at = "applied", timezone.now()
    change.reserved_rent_minor = 0
    change.save()
    event.status, event.applied_at = "applied", timezone.now()
    event.revision += 1
    event.save()
