"""Idempotent opportunity generation and durable, content-free notifications."""

from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from ...models import Lease, ReviewCase, ReviewOpportunity
from ...planning_models import PlanningEvent
from core_apps.properties.models import PropertyVisitReview
from .policy import POLICY, CRITERIA, TAGS, ReviewError
from .eligibility import visit_decision, stay_evidence, overlap_evidence, legacy_exists


def event(item, recipient, kind, suffix=""):
    if recipient is None:
        return
    PlanningEvent.objects.get_or_create(
        recipient=recipient,
        event_key=f"{kind}:{item.id}:{suffix}",
        defaults={
            "destination": {
                "action_type": (
                    "open_review_opportunity"
                    if kind in {"review_opportunity_opened", "review_reminder"}
                    else "open_review_section"
                ),
                "target_id": str(item.id),
                "review_event": kind,
                **(
                    {"review_case_id": suffix}
                    if kind in {"review_report_resolved", "review_appeal_resolved"}
                    else {}
                ),
                **(
                    {"decision_id": suffix}
                    if kind == "review_moderation_decision"
                    else {}
                ),
            }
        },
    )


def target(key, kind, identity):
    return {
        "key": key,
        "kind": kind,
        "id": str(identity),
        "visibility": (
            "public_after_release"
            if kind
            in {
                "property_visit",
                "property_stay",
                "person_landlord",
                "organization_landlord",
            }
            else "private"
        ),
        "criteria": CRITERIA[kind],
        "tag_codes": TAGS[kind],
    }


def _case(
    *,
    key,
    context,
    prop,
    a,
    b,
    recorded,
    snapshot,
    visit=None,
    lease=None,
    peer=None,
    extra=None,
):
    existing = ReviewCase.objects.filter(experience_key=key).first()
    if existing:
        return existing, False
    now = timezone.now()
    days = POLICY[f"{context}_window_days"]
    from .recovery import recovery_context
    from django.utils.dateparse import parse_datetime

    recovery = recovery_context.get()
    if recovery:
        if (
            not parse_datetime(recovery["outage_started_at"])
            <= recorded
            <= parse_datetime(recovery["outage_ended_at"])
        ):
            raise ReviewError("invalid_recovery_evidence", 400)
    elif recorded < now - timedelta(days=days):
        raise ReviewError("review_window_closed")
    # Reconciliation may run late: availability starts now, frozen for the pair.
    snapshot = {
        **snapshot,
        "generation_delay_seconds": max(0, int((now - recorded).total_seconds())),
        "generation_reason": (
            "audited_outage_recovery" if recovery else "canonical_source_reconciliation"
        ),
        **({"recovery": recovery} if recovery else {}),
    }
    item, created = ReviewCase.objects.get_or_create(
        experience_key=key,
        defaults={
            "context_type": context,
            "property": prop,
            "party_a": a,
            "party_b": b,
            "visit": visit,
            "lease": lease,
            "peer_lease": peer,
            "source_snapshot": snapshot,
            "eligible_recorded_at": recorded,
            "opens_at": now,
            "closes_at": now + timedelta(days=days),
            "policy_snapshot": POLICY,
            "release_mode": (
                "after_moderation" if context == "viewing" else "mutual_or_deadline"
            ),
            "gate_released_at": now if context == "viewing" else None,
            **(extra or {}),
        },
    )
    return item, created


def _opportunity(case, person, role, targets, *, legacy=False):
    opp, created = ReviewOpportunity.objects.get_or_create(
        case=case,
        reviewer=person,
        defaults={
            "reviewer_role": role,
            "allowed_targets": targets,
            "state": "revoked" if legacy else "open",
        },
    )
    if created and not legacy:
        event(opp, person, "review_opportunity_opened")
    return opp


@transaction.atomic
def generate_viewing(visit):
    # Lock the immutable source's parent to serialize generation with decisions.
    visit = type(visit).objects.select_for_update().get(pk=visit.pk)
    decision = visit_decision(visit)
    if decision.tenant_id == decision.owner_id:
        raise ReviewError("self_review_forbidden")
    case, _ = _case(
        key=f"viewing:{visit.id}",
        context="viewing",
        prop=visit.property,
        a=visit.tenant,
        b=decision.owner,
        recorded=decision.attested_at,
        visit=visit,
        snapshot={
            "decision_id": str(decision.id),
            "offer_snapshot": decision.offer_snapshot,
            "verification_basis": decision.attendance_source,
        },
    )
    _opportunity(
        case,
        visit.tenant,
        "visitor",
        [target("property", "property_visit", visit.property.id)],
        legacy=PropertyVisitReview.objects.filter(visit=visit).exists(),
    )
    return case


@transaction.atomic
def generate_tenancy(lease):
    from .responsibility import segments
    from .ancestry import for_stay
    from .company_generation import corporate_pair, binding_for_root

    from .eligibility import lock_tenancy

    lease = lock_tenancy(lease)
    binding = binding_for_root(lease)
    if lease.renter_company_id:
        if not binding:
            raise ReviewError("experience_not_confirmed")
        from .corporate_experience import generate

        return generate(binding)
    from ...models import CompanyBookingItem, CompanyLeaseBinding

    if not binding and (
        CompanyBookingItem.objects.filter(
            lease__tenancy_root_id=lease.tenancy_root_id
        ).exists()
        or CompanyLeaseBinding.objects.filter(
            lease__tenancy_root_id=lease.tenancy_root_id
        ).exists()
    ):
        raise ReviewError("experience_not_confirmed")
    cases = []
    for owner, day, end_day, recorded, start, end, previous, change in segments(lease):
        if owner.pk == lease.tenant_id:
            raise ReviewError("self_review_forbidden")
        snapshot = {
            **for_stay(start),
            "move_in_id": str(start.id),
            "move_out_id": str(end.id) if end and not change else None,
            "tenancy_root_id": str(lease.tenancy_root_id),
            "experience_group_id": str(lease.tenancy_root_id),
            "starts_on": day.isoformat(),
            "ends_on": end_day.isoformat(),
            "previous_transition_id": str(previous.id) if previous else None,
            "end_transition_id": str(change.id) if change else None,
        }
        suffix = (
            f":{day}:{change.id if change else 'departure'}"
            if previous or change
            else ""
        )
        key = f"tenancy:{lease.tenancy_root_id}:{owner.pk}{suffix}"
        from .recovery import recovery_context
        from django.utils.dateparse import parse_datetime

        recovery = recovery_context.get()
        if recovery and not parse_datetime(
            recovery["outage_started_at"]
        ) <= recorded <= parse_datetime(recovery["outage_ended_at"]):
            continue
        try:
            if binding:
                case = corporate_pair(binding, lease, owner, recorded, key, snapshot)
            else:
                case, _ = _case(
                    key=key,
                    context="tenancy",
                    prop=lease.property,
                    a=lease.tenant,
                    b=owner,
                    recorded=recorded,
                    lease=lease,
                    snapshot=snapshot,
                )
                _opportunity(
                    case,
                    lease.tenant,
                    "tenant",
                    [
                        target("landlord", "person_landlord", owner.id),
                        target("property", "property_stay", lease.property.id),
                    ],
                    legacy=legacy_exists(lease, lease.tenant),
                )
                _opportunity(
                    case,
                    owner,
                    "landlord",
                    [target("tenant", "person_tenant", lease.tenant.id)],
                    legacy=legacy_exists(lease, owner),
                )
            cases.append(case)
        except ReviewError as error:
            if error.get_codes() != "review_window_closed":
                raise
    if not cases:
        raise ReviewError(
            "occupancy_not_ended" if not segments(lease) else "review_window_closed"
        )
    return cases[-1]


@transaction.atomic
def generate_housemates(a, b):
    a, b = sorted((a, b), key=lambda x: str(x.tenant_id))
    # Fixed row order works for simultaneous A/B and B/A calls.
    rows = {
        x.id: x
        for x in Lease.objects.select_for_update()
        .filter(id__in=[a.id, b.id])
        .order_by("id")
    }
    a, b = rows[a.id], rows[b.id]
    sa, sb, end, day = overlap_evidence(a, b)
    key = f"co_living:{a.tenancy_root_id}:{b.tenancy_root_id}:{day}:{end.possession_on}"
    case, _ = _case(
        key=key,
        context="co_living",
        prop=a.property,
        a=a.tenant,
        b=b.tenant,
        recorded=end.accepted_at,
        lease=a,
        peer=b,
        snapshot={"overlap": [str(sa.id), str(sb.id), str(end.id), day.isoformat()]},
    )
    _opportunity(
        case,
        a.tenant,
        "housemate",
        [target("housemate", "person_housemate", b.tenant.id)],
    )
    _opportunity(
        case,
        b.tenant,
        "housemate",
        [target("housemate", "person_housemate", a.tenant.id)],
    )
    return case
