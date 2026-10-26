"""Post visit decision: continuation."""

from django.utils import timezone
from core_apps.features.models import Lease, OwnerPaymentProfile
from core_apps.features.services.tenancy_invitations import (
    LIVE_LEASE_STATUSES,
    current_invitation_problem,
)
from core_apps.properties.models import Property
from .linked_invitation import DecisionConflict, accommodation_identity


def contracting_problem(visit, decision):
    if visit.company_id:
        return "corporate_contract_policy_required"
    prop = visit.property
    if decision and decision.owner_id != prop.owner_id:
        return "ownership_changed"
    if prop.status != Property.Status.VERIFIED or not prop.is_verified:
        return "property_unavailable"
    if not prop.owner.is_active or not prop.owner.is_verified:
        return "owner_access_changed"
    if not visit.tenant.is_active or not visit.tenant.is_verified:
        return "tenant_access_changed"
    if visit.offer_id:
        offers = (prop.rental_inventory or {}).get("offers", [])
        offer = next(
            (item for item in offers if str(item.get("id")) == visit.offer_id), None
        )
        if (
            not offer
            or offer.get("archived")
            or offer.get("availability") != "available"
        ):
            return "offer_unavailable"
        if visit.offer_snapshot and accommodation_identity(
            offer
        ) != accommodation_identity(visit.offer_snapshot):
            return "accommodation_changed"
        if Lease.objects.filter(
            property=prop, offer_id=visit.offer_id, status__in=LIVE_LEASE_STATUSES
        ).exists():
            return "allocation_conflict"
    return None


def validate_visited_accommodation(visit, snapshot):
    if (
        visit.offer_id
        and visit.offer_snapshot
        and accommodation_identity(snapshot or {})
        != accommodation_identity(visit.offer_snapshot)
    ):
        raise DecisionConflict(
            "The visited accommodation has changed.", "accommodation_changed"
        )


def continuation(
    visit, actor, decision, invitation, ambiguous, actions, legacy_lease=None
):
    owner = actor.pk == visit.property.owner_id
    base = {
        "status": "visit_not_eligible",
        "next_actor": None,
        "next_action": None,
        "blocked_reason": actions["blocked_reason"],
        "source_visit_id": str(visit.id),
        "source_decision_id": str(decision.id) if decision else None,
        "invitation_id": None,
        "agreement_id": None,
        "invoice_id": None,
        "compatibility_version": "visit_decision_v1",
    }
    if visit.company_id:
        from core_apps.features.services.company.viewing_handoff import (
            continuation as company_continuation,
        )

        return company_continuation(visit, actor, decision, base, actions)
    if legacy_lease:
        base.update(
            status=f"agreement_{legacy_lease.status}",
            agreement_id=str(legacy_lease.id),
            next_action="open_agreement",
            next_actor="both",
            blocked_reason=None,
            compatibility_version="historical_v0",
        )
        return base
    if invitation:
        base.update(
            invitation_id=str(invitation.id),
            compatibility_version=invitation.provenance_version,
            blocked_reason=None,
        )
        if invitation.lease_id:
            lease = invitation.lease
            base.update(
                status=f"agreement_{lease.status}",
                agreement_id=str(lease.id),
                next_action="open_agreement",
                next_actor="both",
            )
            if lease.status in {Lease.Status.SIGNED, Lease.Status.ACTIVE}:
                invoice = (
                    lease.invoices.filter(status__in=["due", "overdue"])
                    .order_by("due_date", "created_at")
                    .first()
                )
                if invoice:
                    base.update(invoice_id=str(invoice.id), next_actor="tenant")
                    if not owner:
                        base["next_action"] = "open_invoice"
            return base
        status = invitation.status
        if status in {"pending", "accepted"}:
            if invitation.expires_at <= timezone.now():
                status = "expired"
            else:
                problem = current_invitation_problem(invitation)
                if problem == "property_review_pending":
                    base["blocked_reason"] = problem
                elif problem:
                    status = "revoked"
        base.update(status=f"invitation_{status}", next_action="open_invitation")
        if status == "pending":
            base["next_actor"] = "tenant"
        elif status == "accepted":
            base["next_actor"] = "owner"
            profile = OwnerPaymentProfile.objects.filter(
                owner=visit.property.owner
            ).first()
            if (
                owner
                and not base["blocked_reason"]
                and (
                    not profile
                    or profile.status != "ready"
                    or not profile.payout_ready
                    or "rental-policy-v1" not in profile.accepted_policy_versions
                )
            ):
                base["next_action"] = "setup_owner_payments"
        return base
    if ambiguous:
        base.update(
            status="contracting_blocked",
            blocked_reason="continuation_exists",
            compatibility_version="historical_v0",
        )
    elif decision and decision.value == "decline":
        base.update(status="declined", blocked_reason=None)
    elif decision:
        problem = contracting_problem(visit, decision)
        if problem:
            base.update(status="contracting_blocked", blocked_reason=problem)
        else:
            base.update(
                status="awaiting_owner_invitation",
                blocked_reason=None,
                next_actor="owner",
                next_action="create_rental_invitation" if owner else None,
            )
    elif actions["can_submit"] or (
        actor.pk != visit.tenant_id and visit.status == "confirmed"
    ):
        base.update(
            status="awaiting_tenant_decision",
            blocked_reason=None,
            next_actor="tenant",
            next_action="submit_post_visit_decision" if not owner else None,
        )
    return base


def reason_visible(actor, visit):
    # Owning the property never grants access to the tenant's private text.
    if actor.pk == visit.property.owner_id:
        return False
    from ..viewing_access import participant

    if participant(visit, actor):
        return True
    profile = getattr(actor, "staff_profile", None)
    return bool(
        actor.is_active
        and profile
        and profile.is_active
        and profile.role_name in {"support", "system_owner"}
    )
