"""Read-time work and housing projections. Reads never expire or commit work."""

from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from . import approval_routing, tenancy_access
from .access import member_for
from ..rental_lifecycle.cases import case_queryset


def tenancies(user, company):
    return [
        item
        for item in tenancy_access.visible(user)
        .filter(lease__renter_company=company)
        .select_related("lease", "preparation__booking__request")
        if tenancy_access.roles(item, user)
    ]


def housing_row(item, user):
    roles = tenancy_access.roles(item, user)
    commercial = bool(roles - tenancy_access.PRIVATE_ONLY)
    lease, booking = item.lease, item.preparation.booking
    requirement = booking.request
    assignments = booking.assignments.select_related("employee", "property")
    if not commercial:
        assignments = assignments.filter(employee=user)
    assignments = list(assignments)
    capacity = (
        item.source_snapshot.get("inventory", {}).get("capacity")
        if commercial
        else None
    )
    active = [
        a for a in assignments if a.occupancy_status not in {"returned", "cancelled"}
    ]
    states = {
        state: sum(a.occupancy_status == state for a in active)
        for state in (
            "occupied",
            "arrival_pending",
            "departure_pending",
        )
    }
    states["departure_pending"] = sum(
        a.occupancy_confirmations.filter(kind="departure", state="pending").exists()
        for a in active
    )
    today = timezone.localdate()
    result = {
        "id": str(item.id),
        "lease_id": str(lease.id),
        "title": requirement.title,
        "project_code": requirement.project_code if commercial else "",
        "cost_center": requirement.cost_center if commercial else "",
        "state": lease.status,
        "occupancy_status": lease.occupancy_status,
        "financial_closure_status": lease.financial_closure_status,
        "starts_on": str(lease.start_date),
        "ends_on_exclusive": str(lease.end_date),
        "days_until_end": (lease.end_date - today).days,
        "end_attention": (
            lease.status in {"signed", "active", "termination_pending", "ended"}
            and lease.end_date <= today + timedelta(days=30)
            and (
                lease.occupancy_status != "returned"
                or lease.financial_closure_status != "closed"
            )
        ),
        "commercial_access": commercial,
        "contracted_capacity": capacity,
        "assigned_count": len(active),
        "unassigned_capacity": (
            max(0, capacity - len(active)) if capacity is not None else None
        ),
        **{key + "_count": value for key, value in states.items()},
        "assignments": [
            {
                "id": str(a.id),
                "employee_id": str(a.employee.id),
                "employee_name": a.employee.get_full_name,
                "property_id": str(a.property.id),
                "property_name": a.property.title,
                "state": a.occupancy_status,
                "starts_on": str(a.starts_on),
                "ends_on_exclusive": str(a.ends_on_exclusive),
                # Existing assigned residents may see their arrival address only
                # after agreement activation and their exact assignment consent.
                "arrival_address": (
                    ", ".join(
                        filter(
                            None,
                            [
                                a.property.city.name,
                                a.property.district,
                                a.property.street,
                            ],
                        )
                    )
                    if lease.status == "active"
                    and a.acknowledgment == "accepted"
                    and (
                        a.acknowledged_revision == a.revision
                        or a.occupancy_status == "occupied"
                    )
                    and a.occupancy_status in {"arrival_pending", "occupied"}
                    else None
                ),
                "coordinator_name": item.coordinator.get_full_name,
            }
            for a in assignments
        ],
    }

    from .role_context import selected
    from .role_projections import keep

    role = selected(user, lease.renter_company, required=False)
    if role is None or role == "":
        return result
    fields = {
        "id",
        "title",
        "state",
        "starts_on",
        "ends_on_exclusive",
        "days_until_end",
        "end_attention",
    }
    if role in {"coordinator", "employee"}:
        fields |= {
            "occupancy_status",
            "assignments",
            "assigned_count",
            "arrival_pending_count",
            "departure_pending_count",
            "occupied_count",
        }
    if role == "coordinator":
        fields |= {
            "project_code",
            "cost_center",
            "contracted_capacity",
            "unassigned_capacity",
        }
    if role == "payer":
        fields |= {"financial_closure_status", "lease_id"}
    return {
        **keep(result, fields),
        "commercial_access": role in {"coordinator", "signer", "payer", "approver"},
    }


def payload(user, company):
    member = member_for(user, company)
    from .role_context import permits

    coordinate = permits(member, "coordinator")
    housing = [housing_row(item, user) for item in tenancies(user, company)]
    requests = company.housing_requests.filter(
        Q(coordinator=user) if coordinate else Q(pk__in=[])
    ).order_by("-created_at")
    cases = (
        case_queryset(user)
        .filter(housing_request__company=company)
        .exclude(status="resolved")
        .distinct()
        .order_by("due_at", "id")
    )
    return {
        "company_id": str(company.id),
        "checked_at": timezone.now().isoformat(),
        "work_items": [
            approval_routing.work_payload(row, user)
            for row in approval_routing.work_items(user, company)
        ],
        "requests_without_offers": [
            {"id": str(row.id), "title": row.title, "project_code": row.project_code}
            for row in requests.filter(items__isnull=True)
        ],
        "assistance": [
            {
                "id": str(row.id),
                "title": row.housing_request.title,
                "request_id": str(row.housing_request.id),
                "status": row.status,
                "next_action": row.next_action,
                "due_at": row.due_at.isoformat(),
                "overdue": row.due_at <= timezone.now(),
                "assigned": row.assigned_to_id is not None,
            }
            for row in (cases if coordinate else [])
        ],
        "housing": housing,
        "can_view_costs": any(row["commercial_access"] for row in housing)
        or permits(member, "approver")
        or coordinate,
        "notice_basis": "read_time_30_days_not_contractual_deadline",
    }
