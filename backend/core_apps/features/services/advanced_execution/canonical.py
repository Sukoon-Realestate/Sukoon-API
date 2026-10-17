"""Exact negotiated terms bridge to the existing lease and physical-day engine."""

from datetime import date, timedelta
from uuid import uuid5, NAMESPACE_URL
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.properties.models import Property
from core_apps.users.models import User
from ...models import (
    Lease,
    SigningSession,
    PaymentQuote,
    PaymentAttempt,
    CheckoutSession,
)
from ...providers import get_rental_provider, checkout_available
from ..rental_phase2 import RentalConflict, assert_owner_ready, reserve_inventory_days
from ..rental_phase3 import (
    invoice_balance_minor,
    invoice_payment_allowed,
    quote_fingerprint,
)
from ..tenancy_invitations import resolve_offer_snapshot
from ..rental_lifecycle.inventory import hold_coverage, assert_available
from .plans import record_step


def terms_for(spec, plan):
    start = date.fromisoformat(spec["starts_on"])
    return {
        "starts_on": spec["starts_on"],
        "ends_on_exclusive": spec["ends_on_exclusive"],
        "handover_on": spec["starts_on"],
        "monthly_rent": {
            "amount_minor": spec["rent_minor"],
            "currency": "EGP",
            "exponent": 2,
        },
        "deposit": {
            "amount_minor": spec["deposit_minor"],
            "currency": "EGP",
            "exponent": 2,
        },
        "deposit_holder": "platform",
        "included_services": [],
        "excluded_services": [],
        "termination_policy": {"notice_days": 30},
        "renewal_policy": {"automatic": False},
        "policy_version": "rental-policy-v1",
        "template_id": "eg-residential-v1",
        "template_version": "1",
        "timezone": "Africa/Cairo",
        "occupants": spec.get("metadata", {}).get("occupants", 1),
        "billing_anchor_day": start.day,
        "commission_rate_bps": 1000,
        "commission_payer": "owner",
        "commission_basis": "first_period_base_rent",
        "processing_fee_payer": "platform",
        "renewal_commission_rate_bps": 0,
        "approved_negotiated_terms": {
            "execution_id": str(plan.id),
            "snapshot_digest": plan.digest,
            "source_kind": plan.source_kind,
            "source_id": str(plan.source_id),
            "partial_policy": plan.policy_version,
            "provider_mode": "mock",
        },
    }


def prepare_leg(plan, leg, actor):
    if leg.lease_id:
        return leg
    spec = leg.specification
    prop = get_object_or_404(
        Property.objects.select_for_update(), id=spec["property_id"]
    )
    owner = get_object_or_404(
        User, id=spec["owner_id"], is_active=True, is_verified=True
    )
    tenant = get_object_or_404(
        User, id=spec["tenant_id"], is_active=True, is_verified=True
    )
    assert_owner_ready(owner, prop)
    if (
        prop.status != "verified"
        or not prop.is_verified
        or not prop.is_ownership_verified
        or prop.retired_at
    ):
        raise RentalConflict(
            "The execution inventory is no longer verified and available.",
            code="inventory_changed",
        )
    _, snapshot = resolve_offer_snapshot(
        prop, spec["selection"]["offer_id"], spec["selection"]["offer_revision"]
    )
    from ..planning import selection_payload

    snapshot = selection_payload(snapshot)
    if snapshot != selection_payload(spec["selection"]):
        raise RentalConflict(
            "The reviewed inventory selection changed.", code="offer_changed"
        )
    start, end = date.fromisoformat(spec["starts_on"]), date.fromisoformat(
        spec["ends_on_exclusive"]
    )
    if start < timezone.localdate() or not 1 <= (end - start).days <= 366:
        raise ValidationError("Review current arrival and exclusive departure dates.")
    assert_available(prop, snapshot, start, end)
    for key in ("rent_minor", "deposit_minor"):
        if type(spec[key]) is not int or spec[key] < (1 if key == "rent_minor" else 0):
            raise ValidationError(
                "Agreed rent and deposit must use valid integer minor units."
            )
    from ..student_housing.policies import validate_occupants

    occupants = {
        str(tenant.id),
        *spec.get("metadata", {}).get("required_occupant_ids", []),
    }
    named = list(
        User.objects.filter(id__in=occupants, is_active=True, is_verified=True)
    )
    if len(named) != len(occupants) or spec.get("metadata", {}).get(
        "occupants", len(named)
    ) != len(named):
        raise RentalConflict(
            "Every intended occupant needs a current named account and consent.",
            code="occupant_consent_required",
        )
    validate_occupants(
        prop,
        snapshot,
        named,
        start,
        end,
        occupant_count=spec.get("metadata", {}).get("occupants", len(named)),
    )
    terms = terms_for(spec, plan)
    from ...rental_serializers import RentalTermsSerializer

    validated = RentalTermsSerializer(data=terms)
    validated.is_valid(raise_exception=True)
    # Both actual parties have consented to this unchanged plan; no coordinator
    # consent is copied into an individual signature or payment instruction.
    lease = Lease.objects.create(
        property=prop,
        owner=owner,
        tenant=tenant,
        template_id=terms["template_id"],
        template_version=terms["template_version"],
        start_date=start,
        end_date=end,
        rent_amount_minor=spec["rent_minor"],
        offer_id=snapshot["offer_id"],
        offer_snapshot=snapshot,
        terms=terms,
        policy_version="rental-policy-v1",
        legacy_read_only=False,
        reviewed_by=[str(owner.id), str(tenant.id)],
        hold_expires_at=timezone.now()
        + timedelta(minutes=settings.RENTAL_HOLD_TTL_MINUTES),
    )
    reserve_inventory_days(lease, start, end, lease.hold_expires_at)
    document = get_rental_provider().generate_agreement(lease.id, lease.revision, terms)
    lease.document_id, lease.document_hash, lease.status = (
        document.document_id,
        document.digest,
        Lease.Status.PENDING_SIGNATURES,
    )
    lease.revision += 1
    lease.save()
    leg.lease, leg.canonical_id, leg.state = lease, lease.id, "held"
    leg.save()
    record_step(
        plan,
        leg,
        "canonical_lease_prepared",
        "confirmed",
        "lease",
        lease.id,
        {"hold_expires_at": lease.hold_expires_at.isoformat(), "provider_mode": "mock"},
        actor=actor,
    )
    return leg


def sign(plan, leg, actor, instruction):
    lease = Lease.objects.select_for_update().get(pk=leg.lease_id)
    if actor.pk not in {lease.owner_id, lease.tenant_id}:
        raise PermissionDenied(
            "Only the actual owner or tenant can sign their agreement."
        )
    if lease.status != "pending_signatures" or not hold_coverage(lease):
        raise RentalConflict(
            "Review the current agreement and unexpired hold.", code="hold_expired"
        )
    previous = lease.signing_sessions.filter(
        signer=actor,
        document_id=lease.document_id,
        document_hash=lease.document_hash,
        status="completed",
    ).first()
    if previous:
        return {"signing_session_id": str(previous.id), "lease_id": str(lease.id)}
    key = uuid5(NAMESPACE_URL, instruction.reference)
    hosted = get_rental_provider().create_signing_session(lease.id, actor.id, key)
    session = SigningSession.objects.create(
        lease=lease,
        signer=actor,
        request_key=key,
        lease_revision=lease.revision,
        document_id=lease.document_id,
        document_hash=lease.document_hash,
        hosted_url=hosted.hosted_url,
        provider_session_id=hosted.provider_session_id,
        expires_at=timezone.now()
        + timedelta(minutes=settings.RENTAL_SIGNING_TTL_MINUTES),
    )
    from ...rental_phase2_views_parts.apply_fake_rental_event import (
        apply_fake_rental_event,
    )

    apply_fake_rental_event(
        {
            "type": "signature.completed",
            "provider_session_id": session.provider_session_id,
        }
    )
    return {"signing_session_id": str(session.id), "lease_id": str(lease.id)}


def pay(plan, leg, actor, instruction):
    lease = Lease.objects.select_for_update().get(pk=leg.lease_id)
    if actor.pk != lease.tenant_id:
        raise PermissionDenied(
            "Only the canonical tenant can authorize this rental payment."
        )
    invoice = lease.invoices.filter(billing_period__sequence=1).first()
    if (
        not invoice
        or not checkout_available()
        or not invoice_payment_allowed(actor, invoice)
    ):
        raise RentalConflict(
            "The canonical first rental invoice is not payable.",
            code="payment_unavailable",
        )
    key = uuid5(NAMESPACE_URL, instruction.reference)
    expires = timezone.now() + timedelta(minutes=settings.RENTAL_CHECKOUT_TTL_MINUTES)
    amount = invoice_balance_minor(invoice)
    quote = PaymentQuote.objects.create(
        invoice=invoice,
        request_key=key,
        invoice_revision=invoice.revision,
        payer_amount_minor=amount,
        policy_version="rental-policy-v1",
        expires_at=expires,
        fingerprint=quote_fingerprint(invoice, key, amount, expires),
    )
    attempt = PaymentAttempt.objects.create(
        invoice=invoice,
        payer=actor,
        quote=quote,
        request_key=key,
        invoice_revision=invoice.revision,
        policy_version=quote.policy_version,
        quote_fingerprint=quote.fingerprint,
        amount_minor=amount,
        payment_status="pending",
    )
    hosted = get_rental_provider().create_checkout_session(attempt.id, key)
    CheckoutSession.objects.create(
        invoice=invoice,
        payer=actor,
        attempt=attempt,
        quote=quote,
        request_key=key,
        hosted_url=hosted.hosted_url,
        provider_session_id=hosted.provider_session_id,
        expires_at=expires,
    )
    from ...rental_phase3_views_parts.owner_payables import apply_fake_payment_event

    apply_fake_payment_event(
        {
            "event_id": f"advanced:{instruction.id}:capture",
            "type": "payment.captured",
            "sequence": attempt.revision,
            "payment_attempt_id": str(attempt.id),
            "amount_minor": amount,
            "currency": "EGP",
        }
    )
    return {
        "payment_attempt_id": str(attempt.id),
        "lease_id": str(lease.id),
        "amount_minor": amount,
        "currency": "EGP",
    }
