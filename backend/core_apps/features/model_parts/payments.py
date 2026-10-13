"""Payments models with unchanged Django identities."""

import uuid
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from core_apps.common.models import TimeStampedModel
from .invoices import PaymentQuote
from .invoices import RentInvoice


class PaymentAttempt(TimeStampedModel):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        PENDING = "pending", "Pending"
        AUTHORIZED = "authorized", "Authorized"
        CAPTURED = "captured", "Captured"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"
        CHARGEDBACK = "chargedback", "Charged back"

    invoice = models.ForeignKey(
        RentInvoice, on_delete=models.PROTECT, related_name="payment_attempts"
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_payment_attempts",
    )
    quote = models.ForeignKey(
        PaymentQuote, on_delete=models.PROTECT, related_name="payment_attempts"
    )
    request_key = models.UUIDField()
    revision = models.PositiveIntegerField(default=1)
    invoice_revision = models.PositiveIntegerField()
    policy_version = models.CharField(max_length=40)
    quote_fingerprint = models.CharField(max_length=64)
    payment_status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CREATED
    )
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    settlement_status = models.CharField(max_length=20, default="pending")
    payout_status = models.CharField(max_length=24, default="held")
    provider_attempt_id = models.CharField(max_length=120, blank=True, default="")
    failure_code = models.CharField(max_length=80, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["payer", "invoice", "request_key"],
                name="unique_payment_attempt_request",
            ),
            models.UniqueConstraint(
                fields=["invoice"],
                condition=Q(payment_status__in=["created", "pending", "authorized"]),
                name="unique_live_invoice_payment_attempt",
            ),
        ]


class CheckoutSession(TimeStampedModel):
    invoice = models.ForeignKey(
        RentInvoice, on_delete=models.CASCADE, related_name="checkout_sessions"
    )
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default="pending")
    hosted_url = models.URLField(max_length=500)
    expires_at = models.DateTimeField()
    attempt = models.OneToOneField(
        PaymentAttempt,
        on_delete=models.PROTECT,
        related_name="checkout_session",
        null=True,
        blank=True,
    )
    quote = models.ForeignKey(
        PaymentQuote,
        on_delete=models.PROTECT,
        related_name="checkout_sessions",
        null=True,
        blank=True,
    )
    request_key = models.UUIDField(null=True, blank=True)
    navigation = models.JSONField(default=dict, blank=True)
    return_state = models.CharField(max_length=128, blank=True, default="")
    provider_session_id = models.CharField(max_length=120, blank=True, default="")


class ProviderWebhookEvent(TimeStampedModel):
    provider = models.CharField(max_length=40)
    provider_event_id = models.CharField(max_length=120)
    event_type = models.CharField(max_length=60)
    payment_attempt = models.ForeignKey(
        PaymentAttempt,
        on_delete=models.PROTECT,
        related_name="provider_events",
        null=True,
        blank=True,
    )
    sequence = models.PositiveBigIntegerField(default=0)
    payload_digest = models.CharField(max_length=64)
    signature_valid = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    payload = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_event_id"],
                name="unique_provider_webhook_event",
            )
        ]


class InvoicePaymentAllocation(TimeStampedModel):
    invoice = models.ForeignKey(
        RentInvoice, on_delete=models.PROTECT, related_name="payment_allocations"
    )
    payment_attempt = models.OneToOneField(
        PaymentAttempt, on_delete=models.PROTECT, related_name="invoice_allocation"
    )
    amount_minor = models.PositiveBigIntegerField()
    components = models.JSONField(default=dict, blank=True)


class PaymentReceipt(TimeStampedModel):
    payment_attempt = models.OneToOneField(
        PaymentAttempt, on_delete=models.PROTECT, related_name="receipt"
    )
    status = models.CharField(max_length=20, default="ready")
    title = models.CharField(max_length=160, default="Rent payment receipt")
    revision = models.PositiveIntegerField(default=1)
