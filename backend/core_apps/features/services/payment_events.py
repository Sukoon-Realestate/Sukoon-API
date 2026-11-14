"""Canonical fake-provider event intake, independent of HTTP transport.

Callers must enforce the explicit fake-provider gate and authenticate the event.
Identity reuse, source-domain isolation and canonical processing are shared by
mock checkout, operator tools and authenticated callbacks.
"""

import hashlib
import json
from rest_framework.exceptions import NotFound
from ..models import PaymentAttempt, ProviderWebhookEvent
from .rental_phase2 import RentalConflict
from .rental_phase3 import process_provider_event


def apply_fake_payment_event(payload):
    try:
        attempt = PaymentAttempt.objects.get(id=payload.get("payment_attempt_id"))
    except (PaymentAttempt.DoesNotExist, ValueError):
        raise NotFound()
    if hasattr(attempt, "paymob_payment"):
        raise RentalConflict(
            "Mock events cannot confirm Paymob payments.", code="invalid_payment_domain"
        )
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    event, created = ProviderWebhookEvent.objects.get_or_create(
        provider="fake",
        provider_event_id=str(payload.get("event_id")),
        defaults={
            "event_type": payload.get("type", ""),
            "payment_attempt": attempt,
            "sequence": int(payload.get("sequence", 0)),
            "payload_digest": hashlib.sha256(canonical).hexdigest(),
            "signature_valid": True,
            "payload": payload,
        },
    )
    if not created and event.payload_digest != hashlib.sha256(canonical).hexdigest():
        raise RentalConflict("Provider event ID was reused with different content.")
    process_provider_event(event)
    return {"status": "accepted", "duplicate": not created}


__all__ = ["apply_fake_payment_event"]
