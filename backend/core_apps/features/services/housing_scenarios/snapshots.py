from django.http import Http404

"""Read-only canonical source capture. Do not expire holds or ensure policy here."""

from datetime import timedelta
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ...company_models import (
    CompanyBudgetReservation,
    EmployeeAssignment,
    PortfolioOffer,
)
from ...company_staff_models import CompanyStaffRecord
from ...models import Lease
from ..company.access import member_for
from ..company.offers import resolve_scope, scope_snapshot
from ..rental_lifecycle.common import lifecycle_policy
from ..rental_lifecycle.inventory import assert_available
from ..rental_phase2 import RentalConflict, fingerprint
from ..rental_phase2_parts.remember_mutation import add_months
from .access import request_for

MAX_STAFF, MAX_OFFERS = 40, 12


def staff_for(company):
    return CompanyStaffRecord.objects.filter(
        company=company,
        employment_status="active",
        proposed_roles__contains=["employee"],
    ).select_related("membership__user")


def eligible_staff(company):
    # Python filtering also supports the project's SQLite development database.
    return [
        row
        for row in CompanyStaffRecord.objects.filter(
            company=company, employment_status="active"
        )
        .select_related("membership__user")
        .order_by("display_name", "id")
        if "employee" in row.proposed_roles
        and (
            not row.membership_id
            or (
                row.membership.is_active
                and row.membership.is_employee
                and row.membership.user.is_active
            )
        )
    ]


def offer_snapshot(offer, request, *, turnover_days=0):
    if offer.status != "published":
        raise RentalConflict("Review a published offer.", code="offer_changed")
    props = resolve_scope(offer)
    snapshot = scope_snapshot(offer, props)
    if any(p.occupancy_capacity is None or p.occupancy_capacity < 1 for p in props):
        raise RentalConflict(
            "The selected capacity needs confirmation.", code="capacity_unknown"
        )
    for prop in props:
        assert_available(
            prop,
            {"rental_scope": "entire_property"},
            request.starts_on,
            request.ends_on_exclusive + timedelta(days=turnover_days),
        )
    return snapshot


def capture(user, company, data):
    request = request_for(user, data.get("request_id"), write=True)
    if request.company_id != company.pk:
        raise ValidationError({"request_id": "Choose a request from this company."})
    member = member_for(user, company, "coordinate")
    months = next(
        (
            i
            for i in range(1, 4)
            if add_months(request.starts_on, i) == request.ends_on_exclusive
        ),
        None,
    )
    if months is None or request.starts_on < timezone.localdate():
        raise ValidationError(
            {
                "request_id": "This planning release supports one to three whole future monthly periods."
            }
        )
    staff_ids, offer_ids = data.get("staff_ids"), data.get("offer_ids")
    for key, values, limit in (
        ("staff_ids", staff_ids, MAX_STAFF),
        ("offer_ids", offer_ids, MAX_OFFERS),
    ):
        if (
            not isinstance(values, list)
            or not values
            or len(values) > limit
            or any(not isinstance(v, str) for v in values)
            or len(values) != len(set(values))
        ):
            raise ValidationError(
                {key: f"Choose between 1 and {limit} distinct current records."}
            )
    staff = [row for row in eligible_staff(company) if str(row.id) in staff_ids]
    if len(staff) != len(staff_ids) or len(staff) != request.headcount:
        raise ValidationError(
            {
                "staff_ids": (
                    "Full-coverage planning requires one active eligible staff record "
                    "for every requested person."
                )
            }
        )
    users = [row.membership.user_id for row in staff if row.membership_id]
    protected = (
        EmployeeAssignment.objects.filter(
            employee_id__in=users,
            occupancy_status__in=["occupied", "move_out_pending", "handover_disputed"],
        ).exists()
        or Lease.objects.filter(
            tenant_id__in=users,
            occupancy_status__in=["occupied", "move_out_pending", "handover_disputed"],
        ).exists()
    )
    if protected:
        raise RentalConflict(
            "A confirmed placement needs its authorized transition workflow "
            "before this planning release can relocate it.",
            code="protected_current_placement",
        )
    try:
        policy, rules = lifecycle_policy()
        turnover = rules["turnover_days"]
        policy_version = policy.version
    except RentalConflict:
        raise RentalConflict(
            "Configure the current turnover and date policy before planning.",
            code="policy_not_configured",
        )
    offers = list(PortfolioOffer.objects.filter(id__in=offer_ids).order_by("id"))
    if len(offers) != len(offer_ids):
        raise ValidationError(
            {"offer_ids": "One or more selected offers are unavailable."}
        )
    supply = [
        offer_snapshot(offer, request, turnover_days=turnover) for offer in offers
    ]
    reservations = CompanyBudgetReservation.objects.filter(company=company).filter(
        Q(status="committed")
        | Q(status="reserved", approval__expires_at__gt=timezone.now())
    )
    sums = reservations.aggregate(rent=Sum("rent_minor"), deposit=Sum("deposit_minor"))
    request_sums = reservations.filter(item__request=request).aggregate(
        rent=Sum("rent_minor"), deposit=Sum("deposit_minor")
    )
    rent_max = request.commitment_ceiling_minor - (request_sums["rent"] or 0)
    deposit_max = request.deposit_limit_minor - (request_sums["deposit"] or 0)
    if company.budget_limit_minor is not None:
        rent_max = min(rent_max, company.budget_limit_minor - (sums["rent"] or 0))
    if company.deposit_limit_minor is not None:
        deposit_max = min(
            deposit_max, company.deposit_limit_minor - (sums["deposit"] or 0)
        )
    constraints = data.get("constraints", {})
    if not isinstance(constraints, dict) or set(constraints) - {
        "rent_limit_minor",
        "deposit_limit_minor",
        "allowed_property_ids",
    }:
        raise ValidationError({"constraints": "Use supported explicit constraints."})
    for key, maximum in (
        ("rent_limit_minor", rent_max),
        ("deposit_limit_minor", deposit_max),
    ):
        value = constraints.get(key, max(0, maximum))
        if type(value) is not int or value < 0 or value > maximum:
            raise ValidationError(
                {
                    key: "The cap must be a nonnegative minor-unit amount within current uncommitted policy limits."
                }
            )
        constraints = {**constraints, key: value}
    allowed = constraints.get("allowed_property_ids", {})
    unit_ids = {unit["id"] for offer in supply for unit in offer["units"]}
    if (
        not isinstance(allowed, dict)
        or set(allowed) - set(staff_ids)
        or any(
            not isinstance(v, list)
            or not v
            or any(not isinstance(x, str) for x in v)
            or set(v) - unit_ids
            for v in allowed.values()
        )
    ):
        raise ValidationError(
            {
                "allowed_property_ids": (
                    "Location constraints must reference selected staff "
                    "and canonical selected properties."
                )
            }
        )
    constraints["allowed_property_ids"] = {
        key: sorted(set(value)) for key, value in allowed.items()
    }
    from .assumptions import capture as capture_assumptions

    planning_assumptions = capture_assumptions(user, data, set(staff_ids), unit_ids)
    return {
        "schema": 1,
        "planning_assumptions": planning_assumptions,
        "company_id": str(company.id),
        "company_revision": company.revision,
        "authorization_revision": member.revision,
        "request_id": str(request.id),
        "request_revision": request.revision,
        "request_title": request.title,
        "starts_on": str(request.starts_on),
        "ends_on_exclusive": str(request.ends_on_exclusive),
        "months": months,
        "required_headcount": request.headcount,
        "staff": [
            {
                "id": str(row.id),
                "name": row.display_name,
                "revision": row.revision,
                "membership_revision": (
                    row.membership.revision if row.membership_id else None
                ),
                "membership_status": (
                    "active_member" if row.membership_id else "prepared_staff"
                ),
                "placement_status": "planned",
            }
            for row in sorted(staff, key=lambda row: str(row.id))
        ],
        "offers": supply,
        "constraints": constraints,
        "policy_version": policy_version,
        "turnover_days": turnover,
        "existing_commitments": {
            "rent_minor": sums["rent"] or 0,
            "deposit_minor": sums["deposit"] or 0,
        },
        "assumptions": [
            "selected_supply_only",
            "suitability_requires_human_review",
            "commute_data_unavailable",
            "inventory_not_reserved",
            "fees_transport_moving_costs_unknown",
        ],
        "commute": {"status": "unknown", "source": None, "estimated_minutes": None},
        "execution_available": False,
    }


def source_data(snapshot):
    from .assumptions import source_data as assumption_data

    return {
        "planning_assumptions": assumption_data(
            snapshot.get("planning_assumptions", {})
        ),
        "request_id": snapshot["request_id"],
        "staff_ids": [row["id"] for row in snapshot["staff"]],
        "offer_ids": [row["offer_id"] for row in snapshot["offers"]],
        "constraints": snapshot["constraints"],
    }


def freshness(scenario, user):
    try:
        current = capture(user, scenario.company, source_data(scenario.input_snapshot))
        return "current" if fingerprint(current) == scenario.input_digest else "stale"
    except (ValidationError, RentalConflict, Http404):
        return "stale"
