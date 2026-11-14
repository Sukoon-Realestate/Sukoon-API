"""Original money receipt projections and immutable approval details."""

from core_apps.features.models import RentalPayout
from core_apps.features.models import OwnerPaymentProfile
from core_apps.features.services.rental_phase2 import fingerprint
from .rental_phase6 import refundable_balance_minor


def _money(amount, currency="EGP", exponent=2):
    return {"amount_minor": amount, "currency": currency, "exponent": exponent}


def quote_payload(quote):
    from ..services.chargebacks.funding import quote_disclosure

    return {
        "quote_id": str(quote.id),
        "invoice_id": str(quote.invoice.id),
        "invoice_revision": quote.invoice_revision,
        "payer_amount": _money(
            quote.payer_amount_minor, quote.currency, quote.exponent
        ),
        "tenant_service_fee": _money(
            quote.tenant_service_fee_minor, quote.currency, quote.exponent
        ),
        "policy_version": quote.policy_version,
        "fingerprint": quote.fingerprint,
        "expires_at": quote.expires_at.isoformat(),
        "chargeback_replacement": quote_disclosure(
            quote.invoice, quote.payer_amount_minor
        ),
    }


def payout_payload(item):
    from ..rental_serializers import OwnerPaymentProfileSerializer

    instruction = item.paymob_instructions.filter(current=True).first()
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "status": item.status,
        "amount": _money(item.amount_minor),
        "masked_beneficiary": OwnerPaymentProfileSerializer().get_masked_beneficiary(
            item
        ),
        "reason": item.hold_reason or item.failure_code,
        "submitted_at": (
            instruction.submitted_at.isoformat()
            if instruction and instruction.submitted_at
            else None if instruction else item.created_at.isoformat()
        ),
        "succeeded_at": (
            instruction.confirmed_at.isoformat()
            if instruction and instruction.confirmed_at
            else (
                item.updated_at.isoformat()
                if item.status == RentalPayout.Status.PAID
                else None
            )
        ),
        "history": [
            {"action": value.action, "occurred_at": value.created_at.isoformat()}
            for value in item.audit_events.filter(
                action__in=[
                    "approved",
                    "submitted",
                    "reauthorized",
                    "retry_approved",
                    "paid",
                    "held",
                ]
            ).order_by("pk")
        ],
        "payable_ids": [str(x.id) for x in item.payables.all()],
    }


def refund_payload(item):
    from ..models import PaymobRefund
    from ..services.refund_notifications import history, attempt_history

    instruction = PaymobRefund.objects.filter(refund=item, current=True).first()
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "payment_attempt_id": str(item.payment_attempt.id),
        "revision": item.revision,
        "status": item.status,
        "amount": _money(item.amount_minor),
        "refundable_balance": _money(refundable_balance_minor(item.payment_attempt)),
        "reason": item.reason,
        "provider_refund_id": item.provider_refund_id,
        "failure_code": item.failure_code,
        "instruction_status": instruction.status if instruction else None,
        "history": history(item),
        "attempts": attempt_history(item),
        "allocations": item.allocations,
        "purpose": item.purpose,
        "owner_recovery": _money(
            item.owner_recovery_minor - item.owner_recovered_minor
        ),
    }


def details(refund):
    return {
        "amount_minor": refund.amount_minor,
        "payment_attempt_id": str(refund.payment_attempt.id),
        "allocations": refund.allocations,
        "currency": refund.payment_attempt.currency,
    }


def _details(item):
    from ..services.chargebacks.projection import payable_funding_sources

    profile = OwnerPaymentProfile.objects.filter(owner=item.payout.owner).first()
    return {
        "amount_minor": item.amount_minor,
        "currency": item.currency,
        "recipient_digest": item.recipient_digest,
        "instruction_reference": str(item.reference),
        "beneficiary_revision": profile.revision if profile else None,
        "beneficiary_account_digest": (
            fingerprint(profile.provider_account_id) if profile else None
        ),
        "funding_digest": fingerprint(
            [
                {
                    "id": str(payable.id),
                    "amount_minor": payable.net_minor,
                    "sources": sorted(
                        (str(source.id) for source in payable_funding_sources(payable))
                    ),
                }
                for payable in item.payout.payables.order_by("pk")
            ]
        ),
    }


__all__ = [
    "_details",
    "_money",
    "details",
    "payout_payload",
    "quote_payload",
    "refund_payload",
]
