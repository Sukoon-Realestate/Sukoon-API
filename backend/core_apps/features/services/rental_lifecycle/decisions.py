"""Selection-specific facts and costs. This projection never creates a payable."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.utils import timezone
from ...models import (
    PropertyDecisionFact,
    RentalAvailabilityConfirmation,
    RentalVerificationClaim,
)
from ..rental_phase2 import fingerprint
from ..tenancy_invitations import resolve_offer_snapshot
from .claims import current_claims, claim_current, claim_payload
from .inventory import assert_available


STUDY_FACT_CODES = {
    "study_desk",
    "study_seating",
    "study_lighting",
    "study_storage",
    "room_occupants",
    "shared_facility_occupants",
    "internet_limits",
    "internet_measurement",
    "quiet_hours",
    "shared_study_space",
    "utility_limitations",
}
FACT_CODES = STUDY_FACT_CODES | {
    "furniture_included",
    "private_areas",
    "shared_areas",
    "utility_allocation",
    "internet",
    "rules",
    "access",
    "occupancy",
    "photo_inclusions",
}


def minor(value):
    try:
        amount = Decimal(str(value))
        scaled = amount * 100
        return (
            int(scaled)
            if amount.is_finite()
            and amount >= 0
            and scaled == scaled.to_integral_value()
            else None
        )
    except (InvalidOperation, ValueError, TypeError):
        return None


def cost_line(
    code,
    amount,
    *,
    recurring=False,
    refundable=False,
    source="selected_offer",
    classification=None,
    recurrence=None
):
    return {
        "code": code,
        "amount": (
            {"amount_minor": amount, "currency": "EGP", "exponent": 2}
            if amount is not None
            else None
        ),
        "recurrence": recurrence or ("monthly" if recurring else "once"),
        "payer": "tenant",
        "payee_or_holder": "owner" if code == "rent" else "unknown",
        "due_basis": "billing_schedule" if recurring else "agreement_review",
        "refundable": refundable,
        "source": source,
        "classification": classification
        or ("owner_reported" if amount is not None else "unknown"),
    }


def decision_summary(prop, data, actor=None):
    offer_id, snapshot = resolve_offer_snapshot(
        prop, data["offer_id"], data["offer_revision"]
    )
    terms = snapshot["terms"]
    monthly = terms.get("price_period") == "monthly"
    rent = minor(terms.get("price"))
    deposit = minor(terms.get("deposit"))
    if terms.get("deposit") == "none":
        deposit = 0
    elif (
        monthly
        and rent is not None
        and terms.get("deposit") in {"half_month", "one_month", "two_months"}
    ):
        multiplier = {
            "half_month": Decimal("0.5"),
            "one_month": Decimal(1),
            "two_months": Decimal(2),
        }[terms["deposit"]]
        deposit = int((rent * multiplier).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    lines = [
        cost_line(
            "rent",
            rent,
            recurring=True,
            recurrence=terms.get("price_period") or "unknown",
        ),
        cost_line("deposit", deposit, refundable=True),
        cost_line("utilities", None, recurring=True),
        cost_line("other_services", None, recurring=True),
    ]
    facts = []
    source_facts = {
        item.code: item
        for item in prop.decision_facts.filter(offer_id__in=["", offer_id]).order_by(
            "offer_id"
        )
    }
    for code in sorted(FACT_CODES):
        from django.conf import settings

        if code in STUDY_FACT_CODES and "student_study_facts" not in getattr(
            settings, "STUDENT_ENABLED_SERVICES", []
        ):
            continue
        fact = source_facts.get(code)
        classification = fact.classification if fact else "unknown"
        if fact and (
            (fact.expires_at and fact.expires_at <= timezone.now())
            or (
                classification == "verified"
                and (not fact.claim or not claim_current(fact.claim))
            )
        ):
            classification = "unknown"
        facts.append(
            {
                "id": str(fact.id) if fact else "",
                "revision": fact.revision if fact else 0,
                "offer_id": fact.offer_id if fact else offer_id,
                "code": code,
                "value": fact.value if fact and classification != "unknown" else "",
                "classification": classification,
                "checked_at": fact.checked_at.isoformat() if fact else None,
            }
        )
    confirmation = RentalAvailabilityConfirmation.objects.filter(property=prop).first()
    available, blockers = None, []
    if data.get("starts_on") and data.get("ends_on_exclusive"):
        from ..rental_phase2 import RentalConflict

        try:
            assert_available(
                prop, snapshot, data["starts_on"], data["ends_on_exclusive"]
            )
            available = True
        except RentalConflict as error:
            available = False
            blockers.append(
                str(error.default_code)
                if not error.get_codes()
                else str(error.get_codes())
            )
    claims = [
        claim_payload(item)
        for item in current_claims(
            RentalVerificationClaim.objects.filter(property=prop)
        )
        if claim_current(item)
    ]
    identity = [
        claim_payload(item)
        for item in current_claims(
            RentalVerificationClaim.objects.filter(
                subject_user=prop.owner, subject_kind="identity"
            )
        )
        if claim_current(item)
    ]
    projection = {
        "id": str(prop.id),
        "revision": (prop.rental_inventory or {}).get("revision", 0),
        "selection": snapshot,
        "facts": facts,
        "property_claims": claims,
        "owner_identity_claims": identity,
        "availability_confirmed_at": (
            confirmation.confirmed_at.isoformat()
            if confirmation
            and confirmation.inventory_revision
            == (prop.rental_inventory or {}).get("revision", 0)
            else None
        ),
        "confirmation_revision": confirmation.revision if confirmation else 0,
        "available_for_dates": available,
        "lines": lines,
        "known_monthly_subtotal_minor": (rent if monthly else None),
        "currency": "EGP",
        "exponent": 2,
        "complete_total": False,
        "unresolved_items": [line["code"] for line in lines if line["amount"] is None],
        "allowed_actions": (
            ["confirm_availability", "save_decision_fact"]
            if actor and prop.owner_id == actor.pk
            else []
        ),
        "blocking_reasons": blockers,
    }
    return {
        **projection,
        "digest": fingerprint(projection),
        "generated_at": timezone.now().isoformat(),
    }
