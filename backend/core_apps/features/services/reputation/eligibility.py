"""Derive eligibility only from immutable attendance or bilateral handovers."""

from django.db.models import Q
from django.utils import timezone
from ...models import Lease, RentalHandover, ReviewCase, ReviewOpportunity, RentalReview
from core_apps.properties.models import PropertyVisitDecision, PropertyVisitReview
from .policy import ReviewError


def visit_decision(visit):
    if visit.status != "confirmed" or visit.company_id:
        raise ReviewError("experience_not_confirmed")
    decision = PropertyVisitDecision.objects.filter(
        visit=visit, tenant=visit.tenant, attended=True
    ).first()
    if (
        not decision
        or decision.visit_revision > visit.revision
        or decision.property_id_snapshot != visit.property.id
    ):
        raise ReviewError("experience_not_confirmed")
    return decision


def stay_evidence(lease, *, require_end=True):
    if lease.renter_company_id:
        # Employee experience is derived from EmployeeOccupancyConfirmation.
        # Personal ballots cannot impersonate the corporate renter.
        raise ReviewError("experience_not_confirmed")
    if lease.legacy_read_only:
        raise ReviewError("experience_not_confirmed")
    # Renewals retain tenancy_root_id; the source handovers must be in the same
    # personal responsibility segment, not merely another lease at this address.
    chain = Lease.objects.filter(
        tenancy_root_id=lease.tenancy_root_id,
        owner=lease.owner,
        tenant=lease.tenant,
        property=lease.property,
    )
    evidence = RentalHandover.objects.filter(
        lease__in=chain, status="accepted", accepted_at__isnull=False
    ).order_by("possession_on", "accepted_at")
    parties = {str(lease.owner.id), str(lease.tenant.id)}
    starts = [
        h
        for h in evidence
        if h.kind == "move_in" and parties.issubset(set(h.approvals))
    ]
    ends = [
        h
        for h in evidence
        if h.kind == "move_out" and parties.issubset(set(h.approvals))
    ]
    if not starts:
        raise ReviewError("experience_not_confirmed")
    start = starts[0]
    if start.possession_on > timezone.localdate() or any(
        h.possession_on > timezone.localdate() for h in ends
    ):
        raise ReviewError("experience_not_confirmed")
    end = ends[-1] if ends else None
    if end and (
        end.possession_on < start.possession_on or end.accepted_at < start.accepted_at
    ):
        raise ReviewError("experience_not_confirmed")
    if require_end and (not end or end.lease.occupancy_status != "returned"):
        raise ReviewError("occupancy_not_ended")
    if chain.filter(occupancy_status="handover_disputed").exists():
        raise ReviewError("experience_not_confirmed")
    # Multiple move-ins cannot be interpreted as one uninterrupted interval.
    if len({h.possession_on for h in starts}) > 1:
        raise ReviewError("experience_not_confirmed")
    return start, end


def overlap_evidence(a, b):
    from .company_generation import binding_for_root

    if any(
        (binding_for_root(x) and binding_for_root(x).renter_company_id) for x in (a, b)
    ):
        raise ReviewError("co_living_overlap_insufficient")
    if a.property_id != b.property_id or a.tenant_id == b.tenant_id:
        raise ReviewError("co_living_overlap_insufficient")
    # Property is the canonical unit (building/complex are separate parents).
    # Only explicitly rented rooms/beds prove a shared unit; whole-building
    # portfolio holds, chat membership and plans are not occupancy sources.
    if any(
        (x.offer_snapshot or {}).get("rental_scope") not in {"room", "bed"}
        for x in (a, b)
    ):
        raise ReviewError("co_living_overlap_insufficient")
    if any(
        not isinstance((x.offer_snapshot or {}).get("room_ids"), list)
        or not (x.offer_snapshot or {}).get("room_ids")
        for x in (a, b)
    ):
        raise ReviewError("co_living_overlap_insufficient")
    sa, ea = stay_evidence(a, require_end=False)
    sb, eb = stay_evidence(b, require_end=False)
    ends = [x for x in (ea, eb) if x]
    if not ends:
        raise ReviewError("occupancy_not_ended")
    end = min(ends, key=lambda x: x.possession_on)
    start_day = max(sa.possession_on, sb.possession_on)
    if (end.possession_on - start_day).days < 7:
        raise ReviewError("co_living_overlap_insufficient")
    return sa, sb, end, start_day


def valid_source(case):
    if case.revocation_reason:
        return False
    if case.context_type == "legacy":
        return True
    try:
        if case.company_binding_id or case.employee_assignment_id:
            from .company_generation import valid_company_source

            return valid_company_source(case)
        if case.context_type == "viewing":
            decision = visit_decision(case.visit)
            return (
                str(decision.id) == case.source_snapshot.get("decision_id")
                and decision.owner_id == case.party_b_id
            )
        if case.context_type == "tenancy":
            return valid_tenancy_segment(case)
        if case.context_type == "co_living":
            sa, sb, end, day = overlap_evidence(case.lease, case.peer_lease)
            return [
                str(sa.id),
                str(sb.id),
                str(end.id),
                day.isoformat(),
            ] == case.source_snapshot.get("overlap")
    except ReviewError:
        return False
    return False


def legacy_exists(lease, user):
    return RentalReview.objects.filter(
        lease__tenancy_root_id=lease.tenancy_root_id,
        lease__owner=lease.owner,
        author=user,
    ).exists()


def can_review_lease(lease, user):
    from django.conf import settings

    from ...models import CompanyLeaseBinding, LeaseResponsibilityTransition

    scoped = (
        CompanyLeaseBinding.objects.filter(
            lease__tenancy_root_id=lease.tenancy_root_id
        ).exists()
        or LeaseResponsibilityTransition.objects.filter(
            tenancy_root_id=lease.tenancy_root_id, state="accepted"
        ).exists()
    )
    if scoped:
        return bool(getattr(settings, "REVIEWS_ENABLED", False)) and any(
            valid_source(opp.case)
            for opp in ReviewOpportunity.objects.filter(
                case__lease__tenancy_root_id=lease.tenancy_root_id,
                reviewer=user,
                state="open",
                submitted_once_at__isnull=True,
                case__closes_at__gt=timezone.now(),
            ).select_related("case")
        )
    if (
        not getattr(settings, "REVIEWS_ENABLED", False)
        or user.pk not in {lease.owner_id, lease.tenant_id}
        or legacy_exists(lease, user)
    ):
        return False
    try:
        _, end = stay_evidence(lease)
    except ReviewError:
        return False
    opp = ReviewOpportunity.objects.filter(
        case__experience_key=f"tenancy:{lease.tenancy_root_id}:{lease.owner_id}",
        reviewer=user,
    ).first()
    from datetime import timedelta

    if not opp and end.accepted_at < timezone.now() - timedelta(days=30):
        return False
    return not opp or (
        opp.state == "open"
        and not opp.submitted_once_at
        and opp.case.closes_at > timezone.now()
        and valid_source(opp.case)
    )


def can_review_visit(visit):
    from django.conf import settings

    if (
        not getattr(settings, "REVIEWS_ENABLED", False)
        or PropertyVisitReview.objects.filter(visit=visit).exists()
    ):
        return False
    try:
        decision = visit_decision(visit)
    except ReviewError:
        return False
    opportunity = ReviewOpportunity.objects.filter(
        case__visit=visit, reviewer=visit.tenant
    ).first()
    if opportunity:
        return (
            opportunity.state == "open"
            and not opportunity.submitted_once_at
            and opportunity.case.closes_at > timezone.now()
            and valid_source(opportunity.case)
        )
    from datetime import timedelta

    return decision.attested_at >= timezone.now() - timedelta(days=7)


def valid_tenancy_segment(case):
    from .responsibility import segments

    for owner, day, end_day, _, start, end, previous, change in segments(case.lease):
        snap = case.source_snapshot
        if (
            owner.pk == case.party_b_id
            and case.lease.tenant_id == case.party_a_id
            and str(start.id) == snap.get("move_in_id")
            and (str(end.id) if end and not change else None) == snap.get("move_out_id")
            and day.isoformat() == snap.get("starts_on")
            and end_day.isoformat() == snap.get("ends_on")
            and (str(previous.id) if previous else None)
            == snap.get("previous_transition_id")
            and (str(change.id) if change else None) == snap.get("end_transition_id")
        ):
            return True
    return False


def lock_tenancy(lease):
    """Serialize source changes across all renewals of one continuous tenancy."""
    rows = {
        row.pk: row
        for row in Lease.objects.select_for_update()
        .filter(tenancy_root_id=lease.tenancy_root_id)
        .order_by("pk")
    }
    return rows[lease.pk]
