"""Durable identity for one invoice-linked Paymob checkout."""

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


class PaymobRefund(TimeStampedModel):
    refund = models.OneToOneField(
        "features.RefundRequest", on_delete=models.PROTECT, related_name="paymob_refund"
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


class PaymentFulfillment(TimeStampedModel):
    """Durable service delivery, independent of provider capture."""

    invoice = models.OneToOneField(
        "features.RentInvoice", on_delete=models.PROTECT, related_name="fulfillment"
    )
    attempt = models.OneToOneField(
        "features.PaymentAttempt", on_delete=models.PROTECT, related_name="fulfillment"
    )
    status = models.CharField(max_length=20, default="pending")
    attempts = models.PositiveIntegerField(default=0)
    failure_code = models.CharField(max_length=80, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
