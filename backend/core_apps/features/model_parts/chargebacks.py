"""Original chargeback evidence, replacement funding and restored cash are distinct."""

from django.core.exceptions import ValidationError
from django.db import models
from core_apps.common.models import TimeStampedModel


class RentalChargeback(TimeStampedModel):
    payment_attempt = models.OneToOneField(
        "PaymentAttempt", on_delete=models.PROTECT, related_name="chargeback"
    )
    opening_event = models.OneToOneField(
        "ProviderWebhookEvent", on_delete=models.PROTECT
    )
    provider = models.CharField(max_length=40)
    provider_dispute_id = models.CharField(max_length=120)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3)
    exponent = models.PositiveSmallIntegerField()
    invoice_reopened_minor = models.PositiveBigIntegerField()
    prior_refund_overlap_minor = models.PositiveBigIntegerField(default=0)
    source_snapshot = models.JSONField()
    outcome = models.CharField(max_length=16, default="open")
    outcome_event = models.OneToOneField(
        "ProviderWebhookEvent",
        on_delete=models.PROTECT,
        null=True,
        related_name="decided_chargeback",
    )
    revision = models.PositiveIntegerField(default=1)
    resolved_at = models.DateTimeField(null=True)

    IMMUTABLE = (
        "payment_attempt_id",
        "opening_event_id",
        "provider",
        "provider_dispute_id",
        "amount_minor",
        "currency",
        "exponent",
        "invoice_reopened_minor",
        "prior_refund_overlap_minor",
        "source_snapshot",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_dispute_id"],
                name="unique_provider_chargeback_identity",
            ),
            models.CheckConstraint(
                check=models.Q(outcome__in=["open", "won", "lost", "reversed"]),
                name="chargeback_valid_outcome",
            ),
            models.CheckConstraint(
                check=models.Q(amount_minor__gt=0), name="chargeback_positive_amount"
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            previous = (
                type(self).objects.filter(pk=self.pk).values(*self.IMMUTABLE).first()
            )
            if previous and any(
                previous[key] != getattr(self, key) for key in self.IMMUTABLE
            ):
                raise ValidationError("Original chargeback evidence is immutable.")
        super().save(*args, **kwargs)


class ChargebackReplacementPayment(TimeStampedModel):
    """A new capture funds an existing allocation; it never creates another payable."""

    chargeback = models.ForeignKey(
        RentalChargeback, on_delete=models.PROTECT, related_name="replacement_payments"
    )
    payment_attempt = models.OneToOneField(
        "PaymentAttempt",
        on_delete=models.PROTECT,
        related_name="chargeback_replacement",
    )
    amount_minor = models.PositiveBigIntegerField()
    excess_minor = models.PositiveBigIntegerField(default=0)
    excess_refund = models.OneToOneField(
        "RefundRequest",
        on_delete=models.PROTECT,
        null=True,
        related_name="chargeback_replacement_excess",
    )


class ChargebackRestoration(TimeStampedModel):
    """Authenticated cash receipt, independently of winning the provider dispute."""

    chargeback = models.ForeignKey(
        RentalChargeback, on_delete=models.PROTECT, related_name="restorations"
    )
    provider_event = models.OneToOneField(
        "ProviderWebhookEvent", on_delete=models.PROTECT
    )
    provider = models.CharField(max_length=40)
    cash_reference = models.CharField(max_length=120)
    amount_minor = models.PositiveBigIntegerField()
    invoice_applied_minor = models.PositiveBigIntegerField(default=0)
    overlap_restored_minor = models.PositiveBigIntegerField(default=0)
    excess_minor = models.PositiveBigIntegerField(default=0)
    components = models.JSONField(default=dict)
    excess_refund = models.OneToOneField(
        "RefundRequest",
        on_delete=models.PROTECT,
        null=True,
        related_name="chargeback_restoration",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "cash_reference"],
                name="unique_chargeback_cash_reference",
            )
        ]
