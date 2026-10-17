from django.conf import settings

"""Consented ownership boundaries preserve historical reputation, not payments."""

from datetime import date
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound
from ...models import Lease, LeaseResponsibilityTransition, RentalEvidence, ReviewCase
from .policy import ReviewError, require_actor, revision
from .submission import command, audit


def transitions(lease):
    return LeaseResponsibilityTransition.objects.filter(
        tenancy_root_id=lease.tenancy_root_id, state="accepted"
    ).order_by("effective_on", "id")


def segments(lease):
    from .eligibility import stay_evidence

    start, end = stay_evidence(lease, require_end=False)
    owner, day, previous = lease.owner, start.possession_on, None
    result = []
    for change in transitions(lease):
        if (
            not change.accepted_at
            or change.previous_owner_id != owner.pk
            or change.effective_on < day
        ):
            raise ReviewError("experience_not_confirmed")
        result.append(
            (
                owner,
                day,
                change.effective_on,
                change.accepted_at,
                start,
                end,
                previous,
                change,
            )
        )
        owner, day, previous = change.next_owner, change.effective_on, change
    if end:
        if end.possession_on < day:
            raise ReviewError("experience_not_confirmed")
        result.append(
            (owner, day, end.possession_on, end.accepted_at, start, end, previous, None)
        )
    return result


def current_owner(lease):
    last = transitions(lease).last()
    return last.next_owner if last else lease.owner


def participant(user, item):
    require_actor(user)
    if user.pk not in {item.previous_owner_id, item.next_owner_id, item.tenant_id}:
        raise NotFound()


def payload(item, user):
    participant(user, item)
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "state": item.state,
        "revision": item.revision,
        "effective_on": item.effective_on.isoformat(),
        "previous_owner": item.previous_owner.get_full_name,
        "next_owner": item.next_owner.get_full_name,
        "can_confirm": item.state == "pending" and str(user.id) not in item.approvals,
        "confirmation_count": len(item.approvals),
        "required_confirmations": 3,
    }


def validate_change(item):
    from .eligibility import stay_evidence

    start, end = stay_evidence(item.lease, require_end=False)
    owner = current_owner(item.lease)
    prop = item.lease.property
    prop.refresh_from_db()
    if (
        owner.pk != item.previous_owner_id
        or prop.owner_id != item.next_owner_id
        or not prop.is_ownership_verified
        or item.next_owner_id in {item.tenant_id, owner.pk}
        or item.effective_on < start.possession_on
        or item.effective_on > timezone.localdate()
        or (end and item.effective_on > end.possession_on)
    ):
        raise ReviewError("experience_not_confirmed")
    last = transitions(item.lease).last()
    if last and item.effective_on <= last.effective_on:
        raise ReviewError("experience_not_confirmed")
    # Once a segment has a submission or disclosure it cannot be redrawn.
    cases = ReviewCase.objects.filter(
        lease__tenancy_root_id=item.tenancy_root_id,
        party_b=owner,
        source_snapshot__ends_on__gte=item.effective_on.isoformat(),
    )
    if (
        cases.filter(opportunities__submitted_once_at__isnull=False).exists()
        or cases.filter(closes_at__lte=timezone.now()).exists()
        or cases.filter(gate_released_at__isnull=False).exists()
    ):
        raise ReviewError("review_already_disclosed")
    proof = RentalEvidence.objects.get(pk=item.evidence_id)
    if (
        proof.lease_id != item.lease_id
        or proof.malware_status != "safe"
        or proof.deleted_at
        or not proof.sha256
    ):
        raise ReviewError("experience_not_confirmed")
    return start


def propose(user, lease_id, body):
    require_actor(user)
    lease = get_object_or_404(Lease, id=lease_id)
    owner = current_owner(lease)
    if user.pk not in {lease.tenant_id, owner.pk, lease.property.owner_id}:
        raise NotFound()

    def action():
        from .eligibility import lock_tenancy

        locked = lock_tenancy(lease)
        if LeaseResponsibilityTransition.objects.filter(
            tenancy_root_id=locked.tenancy_root_id, state="pending"
        ).exists():
            raise ReviewError("revision_conflict")
        try:
            day = date.fromisoformat(body.get("effective_on", ""))
        except (ValueError, TypeError):
            raise ReviewError("invalid_review_target", 400)
        evidence = get_object_or_404(
            RentalEvidence, id=body.get("evidence_id"), lease=locked
        )
        item = LeaseResponsibilityTransition(
            lease=locked,
            tenancy_root_id=locked.tenancy_root_id,
            previous_owner=current_owner(locked),
            next_owner=locked.property.owner,
            tenant=locked.tenant,
            effective_on=day,
            evidence=evidence,
        )
        start = validate_change(item)
        item.source_snapshot = {
            "move_in_id": str(start.id),
            "evidence_sha256": evidence.sha256,
        }
        item.save()
        audit(item, user, "ownership_boundary_proposed")
        return payload(item, user)

    return command(user, f"review.ownership.propose.{lease.id}", body, action, lease.id)


def confirm(user, identity, body):
    item = get_object_or_404(LeaseResponsibilityTransition, id=identity)
    participant(user, item)

    def action():
        from .eligibility import lock_tenancy

        lock_tenancy(item.lease)
        locked = LeaseResponsibilityTransition.objects.select_for_update().get(
            pk=item.pk
        )
        participant(user, locked)
        revision(locked, body.get("expected_revision"))
        if locked.state != "pending":
            raise ReviewError("revision_conflict")
        validate_change(locked)
        locked.approvals[str(user.id)] = timezone.now().isoformat()
        required = {
            str(x.id) for x in (locked.previous_owner, locked.next_owner, locked.tenant)
        }
        if required.issubset(locked.approvals):
            locked.state, locked.accepted_at = "accepted", timezone.now()
        locked.revision += 1
        locked.save()
        audit(locked, user, "ownership_boundary_confirmed")
        if locked.state == "accepted" and getattr(settings, "REVIEWS_ENABLED", False):
            # Replace only unsubmitted, undisclosed cases whose period changed.
            ReviewCase.objects.filter(
                lease__tenancy_root_id=locked.tenancy_root_id,
                party_b=locked.previous_owner,
                source_snapshot__ends_on__gte=locked.effective_on.isoformat(),
                revocation_reason="",
            ).update(revocation_reason="ownership_period_replaced")
            from .generation import generate_tenancy

            generate_tenancy(locked.lease)
        return payload(locked, user)

    return command(user, f"review.ownership.confirm.{identity}", body, action, item.id)
