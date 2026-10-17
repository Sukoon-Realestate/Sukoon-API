"""One corporate ballot and independent, deadline-only resident ballots."""

from django.db import transaction
from ...models import CompanyLeaseBinding, ReviewOpportunity, EmployeeAssignment
from .policy import ReviewError


def binding_for_root(lease):
    return CompanyLeaseBinding.objects.filter(
        lease__tenancy_root_id=lease.tenancy_root_id, state="accepted"
    ).first()


def company_opportunity(case, company, role, targets):
    from .generation import event
    from .company_authority import recipients

    opp, created = ReviewOpportunity.objects.get_or_create(
        case=case,
        reviewer_company=company,
        defaults={"reviewer_role": role, "allowed_targets": targets},
    )
    if created:
        for user in recipients(case.company_binding, company, submit=True):
            event(opp, user, "review_opportunity_opened")
    return opp


def corporate_pair(binding, lease, owner, recorded, key, snapshot):
    from .generation import _case, _opportunity, target

    landlord = binding.landlord_company if owner.pk == binding.lease.owner_id else None
    renter = binding.renter_company
    case, _ = _case(
        key=key,
        context="tenancy",
        prop=lease.property,
        a=lease.tenant,
        b=owner,
        recorded=recorded,
        lease=lease,
        snapshot=snapshot,
        extra={
            "company_binding": binding,
            "company": renter,
            "landlord_company": landlord,
        },
    )
    landlord_target = target(
        "landlord",
        "organization_landlord" if landlord else "person_landlord",
        landlord.id if landlord else owner.id,
    )
    tenant_target = target(
        "tenant",
        "organization_renter" if renter else "person_tenant",
        renter.id if renter else lease.tenant.id,
    )
    if renter:
        company_opportunity(case, renter, "company_renter", [landlord_target])
    else:
        _opportunity(
            case,
            lease.tenant,
            "tenant",
            [landlord_target, target("property", "property_stay", lease.property.id)],
        )
    if landlord:
        company_opportunity(case, landlord, "company_landlord", [tenant_target])
    else:
        _opportunity(case, owner, "landlord", [tenant_target])
    return case


@transaction.atomic
def generate_employee(assignment):
    from .employee_occupancy import confirmed, binding as assignment_binding
    from .eligibility import lock_tenancy
    from .generation import _case, _opportunity, target
    from .responsibility import transitions

    lock_tenancy(assignment_binding(assignment).lease)
    assignment = EmployeeAssignment.objects.select_for_update().get(pk=assignment.pk)
    binding, start, end = confirmed(assignment)
    owner, day, previous = binding.lease.owner, start.possession_on, None
    periods = []
    for change in transitions(binding.lease):
        if start.possession_on < change.effective_on < end.possession_on:
            periods.append((owner, day, change.effective_on, previous, change))
            owner, day, previous = change.next_owner, change.effective_on, change
        elif change.effective_on <= start.possession_on:
            owner, previous = change.next_owner, change
    periods.append((owner, day, end.possession_on, previous, None))
    result = []
    for owner, day, until, previous, change in periods:
        landlord = (
            binding.landlord_company if owner.pk == binding.lease.owner_id else None
        )
        case, _ = _case(
            key=f"employee:{assignment.id}:{owner.pk}:{day}",
            context="tenancy",
            prop=assignment.property,
            a=assignment.employee,
            b=owner,
            recorded=end.accepted_at,
            lease=binding.lease,
            snapshot={
                **start.source_snapshot["ancestry"],
                "arrival_id": str(start.id),
                "departure_id": str(end.id),
                "starts_on": day.isoformat(),
                "ends_on": until.isoformat(),
                "experience_group_id": str(binding.lease.tenancy_root_id),
                "previous_transition_id": str(previous.id) if previous else None,
                "end_transition_id": str(change.id) if change else None,
            },
            extra={
                "company_binding": binding,
                "employee_assignment": assignment,
                "landlord_company": landlord,
                "release_mode": "deadline",
            },
        )
        _opportunity(
            case,
            assignment.employee,
            "employee_resident",
            [
                target("property", "property_stay", assignment.property.id),
                target(
                    "landlord",
                    "organization_landlord" if landlord else "person_landlord",
                    landlord.id if landlord else owner.id,
                ),
            ],
        )
        result.append(case)
    return result[-1]


def valid_company_source(case):
    from .eligibility import valid_tenancy_segment
    from .employee_occupancy import confirmed
    from .responsibility import transitions

    binding = case.company_binding
    if not binding or binding.state != "accepted":
        return False
    source = binding.source_snapshot
    if (
        str(binding.lease.owner.id) != source.get("owner_id")
        or str(binding.lease.tenant.id) != source.get("tenant_id")
        or str(binding.lease.document_id) != source.get("document_id")
        or binding.lease.document_hash != source.get("document_hash")
        or binding.lease.status
        not in {"signed", "active", "termination_pending", "ended"}
    ):
        return False
    if not case.employee_assignment_id:
        return valid_tenancy_segment(case)
    assignment = case.employee_assignment
    actual, start, end = confirmed(assignment)
    if (
        actual.pk != binding.pk
        or case.party_a_id != assignment.employee_id
        or case.property_id != assignment.property_id
    ):
        return False
    snap = case.source_snapshot
    if snap.get("arrival_id") != str(start.id) or snap.get("departure_id") != str(
        end.id
    ):
        return False
    owner = binding.lease.owner
    for change in transitions(binding.lease):
        if change.effective_on.isoformat() <= snap["starts_on"]:
            owner = change.next_owner
    return owner.pk == case.party_b_id
