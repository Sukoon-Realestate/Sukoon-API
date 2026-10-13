"""Purpose adapter for non-rent purchases using the shared payment records."""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from ..models import PaymentAttempt, PaymentQuote, SubscriptionPlan
from ..providers import checkout_available, get_rental_provider
from .billing_invoices import authorized_invoice, require_actor
from .billing_settlement import settle_purchase
from .rental_phase2 import RentalConflict
from .rental_phase3 import quote_fingerprint


def validate_payable(invoice, user, revision):
    require_actor(user)
    if not checkout_available():
        raise PermissionDenied({"message": "Mock checkout is unavailable in this environment.", "code": "capability_unavailable"})
    if invoice.purpose == "rent":
        raise RentalConflict("Use the rental invoice checkout for this obligation.")
    if invoice.revision != revision:
        raise RentalConflict("Invoice revision conflict.", code="stale_revision")
    if invoice.status != "due":
        raise RentalConflict("This invoice is not payable.", code="invoice_not_payable")
    if invoice.purpose == "subscription" and not SubscriptionPlan.objects.filter(id=invoice.purchase_snapshot["id"], active=True).exists():
        raise RentalConflict("The selected plan is unavailable.", code="plan_unavailable")
    if invoice.purpose == "advertising":
        from core_apps.advertising.models import Advertisement
        from .billing_advertising import validate_advertisement
        validate_advertisement(get_object_or_404(Advertisement, id=invoice.purchase_snapshot["subject_id"], owner=user))


@transaction.atomic
def quote_purchase(user, invoice_id, body):
    invoice = authorized_invoice(user, invoice_id, lock=True)
    validate_payable(invoice, user, body["expected_revision"])
    existing = PaymentQuote.objects.filter(invoice=invoice, request_key=body["request_key"]).first()
    if existing:
        if existing.invoice_revision != body["expected_revision"]:
            raise RentalConflict("Quote request key conflict.", code="idempotency_conflict")
        return existing
    expiry = timezone.now() + timedelta(minutes=5)
    return PaymentQuote.objects.create(invoice=invoice, request_key=body["request_key"],
        invoice_revision=invoice.revision, payer_amount_minor=invoice.amount_minor,
        currency=invoice.currency, exponent=invoice.exponent, policy_version="purchase-v1",
        fingerprint=quote_fingerprint(invoice, body["request_key"], invoice.amount_minor, expiry), expires_at=expiry)


@transaction.atomic
def checkout_purchase(user, invoice_id, body):
    # Same lock ordering for invoice creation/activation prevents duplicate
    # entitlements across two unpaid invoices or simultaneous workspace calls.
    get_user_model().objects.select_for_update().get(pk=user.pk)
    invoice = authorized_invoice(user, invoice_id, lock=True)
    existing = PaymentAttempt.objects.filter(payer=user, invoice=invoice, request_key=body["request_key"]).select_related("invoice", "quote").first()
    if existing:
        if str(existing.quote.id) != str(body["quote_id"]) or existing.invoice_revision != body["expected_revision"]:
            raise RentalConflict("This request key was used for different data.", code="idempotency_conflict")
        return existing
    validate_payable(invoice, user, body["expected_revision"])
    quote = get_object_or_404(PaymentQuote.objects.select_for_update(), id=body["quote_id"], invoice=invoice)
    if quote.expires_at <= timezone.now():
        raise RentalConflict("The payment quote expired.", code="quote_expired")
    if quote.invoice_revision != invoice.revision or quote.payer_amount_minor != invoice.amount_minor:
        raise RentalConflict("The invoice changed. Review it again.", code="stale_revision")
    attempt = PaymentAttempt.objects.create(invoice=invoice, payer=user, quote=quote,
        request_key=body["request_key"], invoice_revision=invoice.revision,
        policy_version=quote.policy_version, quote_fingerprint=quote.fingerprint,
        amount_minor=quote.payer_amount_minor, currency=quote.currency, exponent=quote.exponent)
    # The adapter validates the isolated provider environment again. No real
    # gateway or card collection is invoked by this flow.
    reference = get_rental_provider().capture_purchase(attempt.id, body["request_key"])
    settle_purchase(invoice, attempt, reference)
    return attempt
