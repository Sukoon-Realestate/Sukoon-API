"""Reputation evidence for a company debtor, retaining original signed history."""

from django.utils import timezone
from core_apps.users.models import User
from ...models import CompanyTenancy
from .policy import ReviewError


def tenancy(binding):
    item = CompanyTenancy.objects.filter(lease=binding.lease).first()
    source, lease = binding.source_snapshot, binding.lease
    if (
        not item
        or binding.state != "accepted"
        or lease.legacy_read_only
        or binding.renter_company_id != lease.renter_company_id
        or not lease.renter_company_id
        or lease.tenant_id
        or lease.status not in {"signed", "active", "termination_pending", "ended"}
        or not source.get("document_id")
        or not source.get("document_hash")
    ):
        raise ReviewError("experience_not_confirmed")
    # Renewal changes the current document. It does not erase the original
    # authoritative signatures from which the company relationship originated.
    required = {source.get("owner_id"), source.get("signer_id")}
    signatures = set(
        map(
            str,
            lease.signing_sessions.filter(
                status="completed",
                completed_at__isnull=False,
                document_id=source["document_id"],
                document_hash=source["document_hash"],
            ).values_list("signer__id", flat=True),
        )
    )
    if None in required or not required.issubset(signatures):
        raise ReviewError("experience_not_confirmed")
    return item


def ownership_changes(item):
    return (
        item.changes.filter(kind="ownership", state="applied")
        .select_related("rental_change")
        .order_by("applied_at", "id")
    )


def owner_periods(binding, start, end, recorded):
    """Half-open civil-date responsibility segments from signed transitions."""
    item = tenancy(binding)
    owner = User.objects.get(id=binding.source_snapshot["owner_id"])
    day, previous, result = start, None, []
    for change in ownership_changes(item):
        body = change.snapshot["content"]
        event = change.rental_change
        if (
            not change.applied_at
            or not event
            or event.status != "applied"
            or not event.document_hash
            or not event.document_id
            or str(owner.id) != body["previous_owner_id"]
            or not {
                body["previous_owner_id"],
                body["new_owner_id"],
                change.snapshot["required"]["signer"],
            }.issubset(event.signed_by)
        ):
            raise ReviewError("experience_not_confirmed")
        boundary = timezone.localtime(change.applied_at).date()
        if boundary > end:
            break
        if boundary > day:
            result.append((owner, day, boundary, change.applied_at, previous, change))
            day = boundary
        owner = User.objects.get(id=body["new_owner_id"])
        previous = change
    if end > day:
        result.append((owner, day, end, recorded, previous, None))
    return result


def handovers(binding):
    item = tenancy(binding)
    rows = list(
        item.lease.handovers.filter(status="accepted", accepted_at__isnull=False)
    )
    sources = {}
    for row in rows:
        snapshot = row.context_snapshot
        change = item.changes.filter(
            id=snapshot.get("source_change_id"), kind=row.kind, state="applied"
        ).first()
        if (
            not change
            or snapshot.get("company_id") != str(binding.renter_company.id)
            or snapshot.get("owner_id") != change.snapshot["required"].get("owner")
            or str(row.possession_on) != change.snapshot["content"]["possession_on"]
            or set(row.approvals) != set(change.snapshot["required"].values())
            or any(
                change.decisions.get(role, {}).get("decision") != "accept"
                for role in change.snapshot["required"]
            )
            or row.possession_on > timezone.localdate()
            or row.kind in sources
        ):
            raise ReviewError("experience_not_confirmed")
        sources[row.kind] = row
    start, end = sources.get("move_in"), sources.get("move_out")
    if not start:
        raise ReviewError("experience_not_confirmed")
    if not end or item.lease.occupancy_status != "returned":
        raise ReviewError("occupancy_not_ended")
    if end.possession_on < start.possession_on or end.accepted_at < start.accepted_at:
        raise ReviewError("experience_not_confirmed")
    return start, end


def generate(binding):
    from .company_generation import corporate_pair

    start, end = handovers(binding)
    result = []
    for owner, day, until, recorded, previous, change in owner_periods(
        binding, start.possession_on, end.possession_on, end.accepted_at
    ):
        result.append(
            corporate_pair(
                binding,
                binding.lease,
                owner,
                recorded,
                f"company-tenancy:{binding.lease.tenancy_root_id}:{owner.id}:{day}",
                {
                    "move_in_id": str(start.id),
                    "move_out_id": str(end.id),
                    "starts_on": str(day),
                    "ends_on": str(until),
                    "experience_group_id": str(binding.lease.tenancy_root_id),
                    "previous_transition_id": str(previous.id) if previous else None,
                    "end_transition_id": str(change.id) if change else None,
                },
            )
        )
    if not result:
        raise ReviewError("experience_not_confirmed")
    return result[-1]


def valid(case):
    binding = case.company_binding
    if case.employee_assignment_id:
        from .employee_occupancy import confirmed

        assignment = case.employee_assignment
        actual, start, end = confirmed(assignment)
        if (
            actual.pk != binding.pk
            or case.party_a_id != assignment.employee_id
            or case.property_id != assignment.property_id
        ):
            return False
        keys = {"arrival_id": str(start.id), "departure_id": str(end.id)}
    else:
        start, end = handovers(binding)
        if (
            case.party_a_id
            or case.company_id != binding.renter_company_id
            or case.property_id != binding.lease.property_id
        ):
            return False
        keys = {"move_in_id": str(start.id), "move_out_id": str(end.id)}
    if any(case.source_snapshot.get(k) != v for k, v in keys.items()):
        return False
    return any(
        owner.pk == case.party_b_id
        and str(day) == case.source_snapshot.get("starts_on")
        and str(until) == case.source_snapshot.get("ends_on")
        for owner, day, until, _, _, _ in owner_periods(
            binding, start.possession_on, end.possession_on, end.accepted_at
        )
    )
