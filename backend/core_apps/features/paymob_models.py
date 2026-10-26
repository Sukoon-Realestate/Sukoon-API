"""Durable identity for one invoice-linked Paymob checkout."""

import uuid
from django.db import models
from core_apps.common.models import TimeStampedModel


class PaymobPayment(TimeStampedModel):
    attempt = models.OneToOneField(
        "features.PaymentAttempt",
        on_delete=models.PROTECT,
        related_name="paymob_payment",
    )
    reference = models.CharField(max_length=100, unique=True)
    integration_id = models.CharField(max_length=18)
    environment = models.CharField(max_length=10, default="sandbox")
    intention_id = models.CharField(max_length=120, blank=True)
    order_id = models.CharField(max_length=18, unique=True, null=True, blank=True)
    transaction_id = models.CharField(max_length=18, unique=True, null=True, blank=True)
    # submitting is committed BEFORE HTTP. Unknown submissions are never retried.
    status = models.CharField(max_length=24, default="submitting")
    failure_code = models.CharField(max_length=80, blank=True)
    reconciled_at = models.DateTimeField(null=True, blank=True)
    renewal_request_id = models.UUIDField(null=True, blank=True)
    renewal_claimed_at = models.DateTimeField(null=True, blank=True)


class PaymobRefund(TimeStampedModel):
    refund = models.ForeignKey(
        "features.RefundRequest",
        on_delete=models.PROTECT,
        related_name="paymob_instructions",
    )
    current = models.BooleanField(default=True)
    retry_of = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="replacement",
    )
    payment = models.ForeignKey(
        PaymobPayment, on_delete=models.PROTECT, related_name="refunds"
    )
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3)
    allocations = models.JSONField()
    refunded_before_minor = models.PositiveBigIntegerField()
    provider_transaction_id = models.CharField(
        max_length=18, null=True, blank=True, unique=True
    )
    status = models.CharField(max_length=20, default="queued")
    failure_code = models.CharField(max_length=80, blank=True)
    authorization_context = models.JSONField(default=dict)
    submitted_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    result_snapshot = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["refund"],
                condition=models.Q(current=True),
                name="one_current_paymob_refund",
            )
        ]


class PaymobPayout(TimeStampedModel):
    """One immutable staging instruction; a missing response never creates another."""

    payout = models.ForeignKey(
        "features.RentalPayout",
        on_delete=models.PROTECT,
        related_name="paymob_instructions",
    )
    current = models.BooleanField(default=True)
    retry_of = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="replacement",
    )
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    account_digest = models.CharField(max_length=64)
    recipient_ciphertext = models.TextField()
    recipient_digest = models.CharField(max_length=64)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    authorization_context = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default="queued", db_index=True)
    provider_transaction_id = models.CharField(
        max_length=80, null=True, blank=True, unique=True
    )
    failure_code = models.CharField(max_length=80, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    next_query_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["payout"],
                condition=models.Q(current=True),
                name="one_current_paymob_payout",
            )
        ]


class PaymentFulfillment(TimeStampedModel):
    """Durable service delivery, independent of provider capture."""

    invoice = models.OneToOneField(
        "features.RentInvoice", on_delete=models.PROTECT, related_name="fulfillment"
    )
    attempt = models.OneToOneField(
        "features.PaymentAttempt", on_delete=models.PROTECT, related_name="fulfillment"
    )
    case = models.OneToOneField(
        "features.RentalOperationalCase",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="fulfillment_job",
    )
    status = models.CharField(max_length=20, default="pending")
    attempts = models.PositiveIntegerField(default=0)
    failure_code = models.CharField(max_length=80, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
