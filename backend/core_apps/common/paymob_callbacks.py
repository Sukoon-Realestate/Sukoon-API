"""Durable verified Paymob callback intake, independent of HTTP responses.

The transport verifies signed provider fields before entering here. Canonical
money state is established only through the existing authenticated inquiry.
"""

from .paymob import BOOLEAN_FIELDS, reported_status
from .paymob_models import PaymobCallbackEvent


def record_verified_callback(values, signature):
    event, created = PaymobCallbackEvent.objects.get_or_create(
        signature=signature.lower(),
        defaults={
            "transaction_id": values["id"],
            "order_id": values["order"],
            "integration_id": values["integration_id"],
            "amount_cents": int(values["amount_cents"]),
            "currency": values["currency"],
            "reported_status": reported_status(values),
            "flags": {key: values[key] == "true" for key in BOOLEAN_FIELDS},
        },
    )
    from core_apps.features.services.paymob_payments import process_callback

    process_callback(event)
    return {"received": True, "duplicate": not created}


__all__ = ["record_verified_callback"]
