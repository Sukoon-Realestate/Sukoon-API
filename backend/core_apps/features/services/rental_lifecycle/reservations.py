"""Free holds and owner blocks share the existing physical allocation authority."""

from datetime import date, timedelta
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from ...models import ReservationHold, RentalAvailabilityConfirmation, TermsProposal
from ..rental_phase2 import RentalConflict, fingerprint
from ..tenancy_invitations import resolve_offer_snapshot
from .common import audit, lifecycle_policy, require_revision
from .inventory import allocate_days, expire_property_holds, unresolved_payment
from .notifications import record_rental_event


def confirmation_current(prop, rules):
    confirmation = RentalAvailabilityConfirmation.objects.filter(property=prop).first()
    return bool(
        confirmation
        and confirmation.inventory_revision
        == (prop.rental_inventory or {}).get("revision", 0)
        and confirmation.confirmed_at
        > timezone.now() - timedelta(hours=rules["availability_hours"])
    )


def confirm_availability(prop, actor, data):
    if prop.owner_id != actor.pk:
        raise NotFound()
    if data["inventory_revision"] != (prop.rental_inventory or {}).get("revision", 0):
        raise RentalConflict("Review the current inventory.", code="stale_revision")
    item, created = RentalAvailabilityConfirmation.objects.get_or_create(
        property=prop,
        defaults={
            "confirmed_by": actor,
            "inventory_revision": data["inventory_revision"],
            "confirmed_at": timezone.now(),
        },
    )
    if not created:
        require_revision(item, data["expected_revision"])
        item.confirmed_at = timezone.now()
        item.confirmed_by = actor
        item.inventory_revision = data["inventory_revision"]
        item.revision += 1
        item.save()
    elif data["expected_revision"] != 0:
        raise RentalConflict("Review the current confirmation.", code="stale_revision")
    audit(item, actor, "availability.confirmed")
    return item


def create_hold(prop, actor, data, *, external=False):
    from core_apps.chat.moderation.policy import require_new_business
    require_new_business(actor)
    require_new_business(prop.owner)
    policy, rules = lifecycle_policy("reservations")
    if not prop.is_verified or prop.status != "verified" or not prop.owner.is_active:
        raise RentalConflict(
            "This property is not currently available.", code="property_unavailable"
        )
    if data["expected_revision"] != 0 or data["inventory_revision"] != (
        prop.rental_inventory or {}
    ).get("revision", 0):
        raise RentalConflict("Review the current inventory.", code="stale_revision")
    if not confirmation_current(prop, rules):
        raise RentalConflict(
            "The owner must confirm current availability.",
            code="availability_confirmation_required",
        )
    offer_id, snapshot = resolve_offer_snapshot(
        prop, data["offer_id"], data["offer_revision"]
    )
    starts, ends = data["starts_on"], data["ends_on_exclusive"]
    if (
        starts < timezone.localdate()
        or not 0 < (ends - starts).days <= rules["max_booking_days"]
    ):
        raise ValidationError(
            {"ends_on_exclusive": "Choose a supported future date range."}
        )
    proposal = None
    if external:
        if prop.owner_id != actor.pk:
            raise NotFound()
        if not data.get("reason", "").strip():
            raise ValidationError(
                {"reason": "Describe the external booking or operational block."}
            )
    else:
        proposal = (
            TermsProposal.objects.select_for_update()
            .filter(
                id=data.get("proposal_id"),
                interest__property=prop,
                interest__tenant=actor,
                status="accepted",
            )
            .first()
        )
        if not proposal:
            raise NotFound()
        require_revision(proposal, data.get("proposal_revision"))
        if (
            proposal.offer_snapshot != snapshot
            or proposal.terms["starts_on"] != starts.isoformat()
            or proposal.terms["ends_on_exclusive"] != ends.isoformat()
        ):
            raise RentalConflict(
                "The accepted terms no longer match this selection.",
                code="document_changed",
            )
        if data.get("terms_digest") != fingerprint(proposal.terms):
            raise RentalConflict("Review the accepted terms.", code="document_changed")
        if (
            proposal.interest.status in {"withdrawn", "rejected"}
            or proposal.invitations.filter(lease__isnull=False).exists()
        ):
            raise RentalConflict(
                "This application cannot start a new reservation.",
                code="source_changed",
            )
    expire_property_holds(prop)
    if (
        not external
        and ReservationHold.objects.filter(
            actor=actor, status__in=["active", "reconciliation_pending"]
        ).count()
        >= rules["max_active_holds"]
    ):
        raise RentalConflict(
            "Resolve an existing reservation before starting another.",
            code="hold_limit_reached",
        )
    hold = ReservationHold.objects.create(
        property=prop,
        actor=actor,
        proposal=proposal,
        offer_id=offer_id,
        offer_revision=data["offer_revision"],
        inventory_revision=data["inventory_revision"],
        selection_snapshot=snapshot,
        terms_digest=(
            fingerprint(proposal.terms)
            if proposal
            else fingerprint(
                {"selection": snapshot, "starts_on": starts, "ends_on": ends}
            )
        ),
        starts_on=starts,
        ends_on_exclusive=ends,
        blocked_until_exclusive=ends + timedelta(days=rules["turnover_days"]),
        kind=data.get("kind", "external_booking") if external else "reservation",
        policy_version=policy.version,
        policy_snapshot=rules,
        expires_at=(
            None
            if external
            else timezone.now() + timedelta(minutes=rules["hold_minutes"])
        ),
        reason=data.get("reason", ""),
    )
    allocate_days(
        prop=prop,
        snapshot=snapshot,
        offer_id=offer_id,
        starts_on=starts,
        ends_on=hold.blocked_until_exclusive,
        expires_at=hold.expires_at,
        hold=hold,
    )
    audit(hold, actor, "reservation.created")
    record_rental_event(
        hold, {actor, prop.owner}, "reservation.created", "open_reservation_hold"
    )
    return hold


def hold_actions(hold, actor):
    if hasattr(hold, "companybookingitem"):
        return []
    if hold.status != "active" or hold.lease_id:
        return []
    if hold.expires_at and hold.expires_at <= timezone.now():
        return []
    if actor.pk not in {hold.actor_id, hold.property.owner_id}:
        return []
    actions = ["release_hold"]
    if (
        actor.pk == hold.actor_id
        and hold.kind == "reservation"
        and hold.extension_count < hold.policy_snapshot["max_extensions"]
    ):
        actions.append("extend_hold")
    return actions


def hold_payload(hold, actor):
    actions = hold_actions(hold, actor)
    return {
        "id": str(hold.id),
        "revision": hold.revision,
        "property_id": str(hold.property.id),
        "proposal_id": str(hold.proposal.id) if hold.proposal else None,
        "lease_id": str(hold.lease.id) if hold.lease else None,
        "status": hold.status,
        "kind": hold.kind,
        "selection": hold.selection_snapshot,
        "starts_on": hold.starts_on.isoformat(),
        "ends_on_exclusive": hold.ends_on_exclusive.isoformat(),
        "blocked_until_exclusive": hold.blocked_until_exclusive.isoformat(),
        "expires_at": hold.expires_at.isoformat() if hold.expires_at else None,
        "server_time": timezone.now().isoformat(),
        "policy_version": hold.policy_version,
        "terms_digest": hold.terms_digest,
        "reconciliation_deadline": (
            hold.reconciliation_deadline.isoformat()
            if hold.reconciliation_deadline
            else None
        ),
        "amount_due_now": {"amount_minor": 0, "currency": "EGP", "exponent": 2},
        "allowed_actions": actions,
        "blocking_reasons": (
            ["reconciliation_required"]
            if hold.status == "reconciliation_pending"
            else []
        ),
    }


def change_hold(hold, actor, data, action):
    expire_property_holds(hold.property)
    hold.refresh_from_db()
    require_revision(hold, data["expected_revision"])
    if action not in hold_actions(hold, actor):
        raise RentalConflict(
            "This reservation action is no longer available.", code="hold_changed"
        )
    if action == "extend_hold":
        lifecycle_policy("reservations")
        if not confirmation_current(hold.property, hold.policy_snapshot):
            raise RentalConflict(
                "Availability needs a new confirmation.",
                code="availability_confirmation_required",
            )
        if hold.proposal and (
            hold.proposal.status != "accepted"
            or fingerprint(hold.proposal.terms) != hold.terms_digest
        ):
            raise RentalConflict("Review the changed terms.", code="document_changed")
        resolve_offer_snapshot(hold.property, hold.offer_id, hold.offer_revision)
        hold.expires_at = timezone.now() + timedelta(
            minutes=hold.policy_snapshot["hold_minutes"]
        )
        hold.extension_count += 1
        hold.day_locks.update(expires_at=hold.expires_at)
    else:
        if hold.lease_id and unresolved_payment(hold.lease):
            raise RentalConflict(
                "Reconcile payment before releasing this reservation.",
                code="reconciliation_required",
            )
        hold.day_locks.all().delete()
        hold.status = "released"
        hold.released_at = timezone.now()
    hold.revision += 1
    hold.save()
    audit(hold, actor, action, data.get("reason", ""))
    record_rental_event(
        hold, {hold.actor, hold.property.owner}, action, "open_reservation_hold"
    )
    return hold


def transfer_hold(lease, proposal):
    if proposal is None:
        return False
    """Caller holds property root. Reassign rows, never double allocate."""
    hold = (
        ReservationHold.objects.select_for_update()
        .filter(
            proposal=proposal,
            actor=lease.tenant,
            status="active",
            lease__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .first()
    )
    if not hold:
        return False
    if (
        hold.selection_snapshot != lease.offer_snapshot
        or hold.terms_digest != fingerprint(lease.terms)
    ):
        raise RentalConflict(
            "The reservation and agreement differ.", code="document_changed"
        )
    if hold.starts_on != lease.start_date or hold.ends_on_exclusive != lease.end_date:
        raise RentalConflict(
            "The reservation dates have changed.", code="document_changed"
        )
    lease.hold_expires_at = hold.expires_at
    lease.save(update_fields=["hold_expires_at", "updated_at"])
    hold.lease = lease
    hold.revision += 1
    hold.save()
    hold.day_locks.update(lease=lease)
    return True
