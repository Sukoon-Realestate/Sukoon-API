from django.utils import timezone
from ..providers import checkout_available


def invoice_payload(invoice, user, language="en", *, mobile=False):
    is_rent = invoice.purpose == "rent"
    # Rental settlement credits reduce the obligation without rewriting its
    # original amount or treating the credit as a cash payment.
    total_minor = invoice.amount_minor - (invoice.credits_minor if is_rent else 0)
    payable = invoice.status in {"due", "overdue", "partially_paid"}
    if is_rent:
        from .rental_phase3 import invoice_payment_allowed

        payable = invoice_payment_allowed(user, invoice)
    else:
        payable = (
            payable
            and invoice.payer_id == user.pk
            and user.is_active
            and checkout_available()
        )
    cancellable = (
        not is_rent
        and invoice.status == "due"
        and invoice.payer_id == user.pk
        and user.is_active
    )
    receipt = (
        invoice.payment_attempts.filter(payment_status="captured")
        .select_related("receipt")
        .first()
    )
    payload = {
        "id": str(invoice.id),
        "reference": invoice.reference,
        "purpose": invoice.purpose,
        "workspace": invoice.workspace,
        "status": invoice.status,
        "revision": invoice.revision,
        "currency": invoice.currency,
        "exponent": invoice.exponent,
        "total_minor": total_minor,
        "paid_minor": invoice.applied_minor,
        "balance_minor": max(0, total_minor - invoice.applied_minor),
        "issued_at": invoice.created_at.isoformat(),
        "due_date": invoice.due_date.isoformat(),
        "paid_at": (
            receipt.confirmed_at.isoformat()
            if receipt and receipt.confirmed_at
            else None
        ),
        "receipt_id": (
            str(receipt.receipt.id) if receipt and hasattr(receipt, "receipt") else None
        ),
        "provider_mode": (
            "mock"
            if receipt and receipt.provider_attempt_id.startswith("mock-")
            else None
        ),
        "allowed_actions": (["pay"] if payable else [])
        + (["cancel"] if cancellable else []),
        "lines": [
            {
                "id": str(line.id),
                "description": (
                    line.source.get("description_ar", line.description)
                    if language == "ar"
                    else line.description
                ),
                "quantity": line.source.get("quantity", 1),
                "amount_minor": line.amount_minor,
                "currency": line.currency,
                "exponent": line.exponent,
            }
            for line in invoice.lines.all()
        ],
        "purchase": invoice.purchase_snapshot,
        "source": {
            "kind": "rent_invoice" if is_rent else invoice.purpose,
            "id": (
                str(invoice.id)
                if is_rent
                else invoice.purchase_snapshot.get(
                    "subject_id", invoice.purchase_snapshot.get("id")
                )
            ),
        },
    }

    if mobile:
        # These immutable source snapshots remain in storage and in the legacy
        # projection. Mobile renders the authoritative invoice/line amounts.
        payload.pop("purchase")
    return payload


def purchase_attempt_payload(attempt):
    receipt = getattr(attempt, "receipt", None)
    return {
        "id": str(attempt.id),
        "invoice_id": str(attempt.invoice.id),
        "request_key": str(attempt.request_key),
        "quote_id": str(attempt.quote.id),
        "revision": attempt.revision,
        "status": attempt.payment_status,
        "payment_status": attempt.payment_status,
        "provider_mode": "mock",
        "provider_reference": attempt.provider_attempt_id,
        "amount_minor": attempt.amount_minor,
        "currency": attempt.currency,
        "exponent": attempt.exponent,
        "receipt_id": str(receipt.id) if receipt else None,
        "confirmed_at": (
            attempt.confirmed_at.isoformat() if attempt.confirmed_at else None
        ),
    }


def purchase_quote_payload(quote):
    return {
        "id": str(quote.id),
        "invoice_id": str(quote.invoice.id),
        "invoice_revision": quote.invoice_revision,
        "amount_minor": quote.payer_amount_minor,
        "currency": quote.currency,
        "exponent": quote.exponent,
        "expires_at": quote.expires_at.isoformat(),
        "provider_mode": "mock",
    }
