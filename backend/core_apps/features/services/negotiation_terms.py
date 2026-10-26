"""Versioned bilateral terms; acceptance never allocates physical inventory."""

import copy
from datetime import date

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from ..models import TermsProposal, TermsProposalVersion, ReservationHold
from .rental_phase2 import RentalConflict, add_months, validate_interest_capacity
from .rental_lifecycle.common import require_revision, require_actor, audit
from .rental_lifecycle.consents import record_consent
from .rental_lifecycle.notifications import record_rental_event

# The existing eg-residential-v1 canonical document already uses these clauses
# (advanced_execution.canonical.terms_for). They are not negotiation inputs.
FIXED_TEMPLATE_TERMS = {
    "termination_policy": {"notice_days": 30},
    "renewal_policy": {"automatic": False},
}
NEGOTIABLE = {
    "monthly_rent", "deposit", "starts_on", "ends_on_exclusive", "handover_on",
    "included_services", "excluded_services", "occupants", "billing_anchor_day",
}


def is_expired(proposal):
    return proposal.expires_at is not None and proposal.expires_at <= timezone.now()


def stage_started(proposal):
    return (
        proposal.invitations.filter(status__in=["pending", "accepted"]).exists()
        or proposal.invitations.filter(lease__isnull=False).exists()
        or ReservationHold.objects.filter(
            proposal=proposal, status__in=["active", "reconciliation_pending", "committed"],
        ).exists()
    )


def require_followup(proposal, *, continue_hold=False):
    if proposal.status != TermsProposal.Status.ACCEPTED:
        raise RentalConflict("Both parties must accept this version first.", code="terms_not_accepted")
    if proposal.expires_at is None:
        raise RentalConflict("Review a proposal with an explicit deadline.", code="terms_deadline_required")
    continuing = continue_hold and ReservationHold.objects.filter(
        proposal=proposal, status="active", expires_at__gt=timezone.now(),
        created_at__lt=proposal.expires_at,
    ).exists()
    if is_expired(proposal) and not continuing:
        raise RentalConflict("The negotiated terms expired. Obtain a new proposal.", code="terms_expired")


def record_version(proposal, *, baseline=False):
    return TermsProposalVersion.objects.get_or_create(
        proposal=proposal, version=proposal.content_revision,
        defaults={"author_id": proposal.author_id or proposal.owner_id,
                  "terms": copy.deepcopy(proposal.terms),
                  "offer_snapshot": copy.deepcopy(proposal.offer_snapshot),
                  "expires_at": proposal.expires_at, "baseline": baseline},
    )[0]


def policy_terms(terms):
    import json

    for field, expected in FIXED_TEMPLATE_TERMS.items():
        value = terms.get(field)
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                pass
        if value != expected:
            raise ValidationError({field: "This clause follows the published template and cannot be negotiated."})
        terms[field] = copy.deepcopy(expected)
    return terms


def validate(interest, terms, snapshot, deadline, *, previous=None):
    from .rental_lifecycle.terms import _json_safe

    if deadline is None or deadline <= timezone.now():
        raise ValidationError({"expires_at": "Choose an explicit future deadline."})
    if snapshot.get("terms", {}).get("price_period") != "monthly":
        raise ValidationError({"offer_id": "This workflow supports monthly accommodation."})
    terms = policy_terms(_json_safe(terms))
    if (terms.get("template_id"), terms.get("template_version")) != ("eg-residential-v1", "1"):
        raise ValidationError({"template_id": "Choose the supported contract template."})
    validate_interest_capacity(snapshot, terms["occupants"])
    if terms["monthly_rent"]["amount_minor"] <= 0:
        raise ValidationError({"monthly_rent": "Specify a positive agreed rent."})
    start, end = date.fromisoformat(terms["starts_on"]), date.fromisoformat(terms["ends_on_exclusive"])
    if start < timezone.localdate() or not start < end <= add_months(start, 60):
        raise ValidationError({"ends_on_exclusive": "Use a supported future rental interval."})
    if previous:
        for field in set(previous.terms) | set(terms):
            if field not in NEGOTIABLE and previous.terms.get(field) != terms.get(field):
                raise ValidationError({field: "This field is not a negotiable rental term."})
    if interest.academic_plan_id:
        from .student_housing.access import plan_for
        from .student_housing.plans import blockers

        plan = plan_for(interest.tenant, interest.academic_plan.id)
        if (plan.requirements_revision != interest.academic_revision or blockers(plan)
                or start != plan.starts_on or end != plan.ends_on_exclusive or terms["occupants"] != 1
                or terms["monthly_rent"]["amount_minor"] > (plan.criteria.get("budget_max") or {}).get("amount_minor", 0)):
            raise RentalConflict(
                "Review the affected academic requirements and approvals first.", code="academic_review_required",
            )
    return terms


def with_context(snapshot, prop):
    return {**snapshot, "negotiation_context": {
        "owner_id": str(prop.owner.id),
        "governorate_id": prop.governorate_id,
        "city_id": prop.city_id,
        "district": prop.district_catalog_id or prop.district,
        "latitude": str(prop.latitude) if prop.latitude is not None else None,
        "longitude": str(prop.longitude) if prop.longitude is not None else None,
    }}


def material_selection(snapshot):
    return {**{key: snapshot.get(key) for key in (
        "property_id", "offer_id", "rental_scope", "room_ids", "bed_id", "capacity",
        "bathroom_access", "availability", "archived", "negotiation_context",
    )}, "eligibility": {key: snapshot.get("terms", {}).get(key) for key in (
        "price_period", "suitable_for", "smoking_allowed", "rules",
    )}}


def with_physical_context(snapshot, prop):
    from core_apps.properties.services.viewing_listing_changes import source_state
    from .rental_lifecycle.terms import _json_safe

    selected = with_context(snapshot, prop)
    source = source_state(prop, str(snapshot.get("offer_id", "")))
    selected["negotiation_context"]["physical_source"] = _json_safe({
        key: source[key] for key in ("location", "accommodation")
    })
    return selected


def current_selection(proposal, *, expected_snapshot=None):
    from .tenancy_invitations import resolve_offer_snapshot

    prop = proposal.interest.property
    if proposal.interest.academic_plan_id:
        from .student_housing.access import plan_for
        from .student_housing.plans import blockers
        plan = plan_for(proposal.interest.tenant, proposal.interest.academic_plan.id)
        if plan.requirements_revision != proposal.interest.academic_revision or blockers(plan):
            raise RentalConflict("Review the current academic requirements first.", code="academic_review_required")
    current_offer = next((row for row in (prop.rental_inventory or {}).get("offers", [])
                          if str(row.get("id")) == proposal.interest.offer_id), None)
    if current_offer is None:
        raise RentalConflict("The selected accommodation is unavailable.", code="offer_unavailable")
    snapshot = resolve_offer_snapshot(prop, proposal.interest.offer_id, current_offer["revision"])[1]
    if proposal.author_id:
        expected = expected_snapshot or proposal.offer_snapshot
        context = expected.get("negotiation_context", {})
        snapshot = (with_physical_context if "physical_source" in context else with_context)(snapshot, prop)
        if material_selection(snapshot) != material_selection(expected_snapshot or proposal.offer_snapshot):
            raise RentalConflict("Review the changed accommodation and eligibility.", code="accommodation_changed")
    elif snapshot != (expected_snapshot or proposal.offer_snapshot):
        raise RentalConflict("Review the changed accommodation.", code="accommodation_changed")
    return snapshot


def participant_ids(interest):
    return {interest.tenant_id, interest.property.owner_id}


def active_negotiation(interest):
    from django.db.models import Q
    return interest.terms_proposals.filter(
        status__in=["proposed", "changes_requested", "accepted"],
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        | Q(reservation_holds__status__in=["active", "reconciliation_pending", "committed"])
        | Q(invitations__status__in=["pending", "accepted"])
        | Q(invitations__lease__isnull=False),
    ).exists()


def actions(user, proposal):
    if (not user or not user.is_active or not user.is_verified
            or user.pk not in participant_ids(proposal.interest)):
        return []
    if proposal.status in {"withdrawn", "rejected", "expired", "superseded"} or is_expired(proposal):
        return []
    if stage_started(proposal):
        return []
    if proposal.interest.status in {"withdrawn", "rejected"}:
        return []
    if proposal.status == "accepted":
        return ["withdraw"]
    author = proposal.author_id or proposal.owner_id
    if user.pk == author:
        return ["edit_terms", "withdraw"]
    result = ["counter_terms", "reject", "request_changes"]
    if proposal.expires_at is not None and str(user.id) not in proposal.accepted_by:
        result.append("accept")
    return result


def notify(proposal, actor, action):
    recipients = {proposal.owner, proposal.interest.tenant} - {actor}
    record_rental_event(proposal, recipients, action, "open_rental_terms")


def expire_due():
    from django.db import transaction
    from core_apps.properties.models import Property

    count = 0
    candidates = TermsProposal.objects.filter(
        author__isnull=False, expires_at__lte=timezone.now(),
        status__in=["proposed", "changes_requested", "accepted"],
    ).values_list("pk", "interest__property_id")
    for pk, property_id in candidates.iterator():
        with transaction.atomic():
            Property.objects.select_for_update().get(pk=property_id)
            proposal = TermsProposal.objects.select_for_update().select_related("owner", "interest__tenant").get(pk=pk)
            if not is_expired(proposal) or proposal.status not in {"proposed", "changes_requested", "accepted"} or stage_started(proposal):
                continue
            proposal.status = "expired"
            proposal.revision += 1
            proposal.save(update_fields=["status", "revision", "updated_at"])
            notify(proposal, None, "terms.expired")
            count += 1
    return count


def revise(proposal, actor, data, snapshot):
    require_actor(actor)
    require_revision(proposal, data["expected_revision"])
    action = data.get("action", "edit_terms")
    if action not in actions(actor, proposal) or action not in {"edit_terms", "counter_terms"}:
        raise PermissionDenied("Only an eligible author or counterparty may propose this version.")
    terms = validate(proposal.interest, data["terms"], snapshot, data["expires_at"], previous=proposal)
    record_version(proposal, baseline=not proposal.author_id)
    proposal.previous_terms = [*proposal.previous_terms, copy.deepcopy(proposal.terms)]
    proposal.terms, proposal.offer_snapshot = terms, snapshot
    proposal.content_revision += 1
    proposal.revision += 1
    proposal.author = actor
    proposal.expires_at = data["expires_at"]
    proposal.status = "proposed"
    proposal.accepted_by = [str(actor.id)]
    proposal.save()
    record_version(proposal)
    record_consent(proposal, actor, "propose", {
        "content_version": proposal.content_revision, "terms": terms,
        "selection": snapshot, "expires_at": proposal.expires_at.isoformat(),
    })
    audit(proposal, actor, "terms.version_proposed")
    notify(proposal, actor, "terms.changed")
    return proposal


def respond(proposal, actor, data):
    require_actor(actor)
    require_revision(proposal, data["expected_revision"])
    decision = data["decision"]
    if decision not in actions(actor, proposal):
        raise RentalConflict("Review the current negotiation and its deadline.", code="invalid_state")
    if decision == "withdraw" and not data.get("note", "").strip():
        raise ValidationError({"note": "Explain why you are withdrawing."})
    if decision == "accept":
        from core_apps.users.services.new_business import require_new_business
        from core_apps.chat.moderation.policy import require_business_participants

        require_new_business(*participant_ids(proposal.interest))
        require_business_participants(proposal.owner, proposal.interest.tenant)
        current_selection(proposal)
        proposal.accepted_by = list(dict.fromkeys([*proposal.accepted_by, str(actor.id)]))
        required = {str(proposal.owner.id), str(proposal.interest.tenant.id)}
        proposal.status = "accepted" if required <= set(proposal.accepted_by) else "proposed"
    elif decision == "request_changes":
        proposal.status, proposal.accepted_by = "changes_requested", []
    elif decision == "reject":
        proposal.status = "rejected"
    elif decision == "withdraw":
        proposal.status, proposal.withdrawal_reason = "withdrawn", data["note"].strip()
    else:
        raise ValidationError({"decision": "Use the proposal editor for a counter-offer."})
    record_consent(proposal, actor, decision, {
        "content_version": proposal.content_revision, "terms": proposal.terms,
        "selection": proposal.offer_snapshot, "expires_at": proposal.expires_at.isoformat() if proposal.expires_at else None,
        "note": data.get("note", "").strip(),
    })
    proposal.revision += 1
    proposal.save(update_fields=["status", "accepted_by", "revision", "withdrawal_reason", "updated_at"])
    audit(proposal, actor, "terms." + decision, data.get("note", ""))
    notify(proposal, actor, "terms." + decision)
    return proposal
