"""Company mandates and exact pre-contract consent; no provider effects implied."""

from django.conf import settings
from django.db import models
from django.db.models import Q, F
from core_apps.common.models import TimeStampedModel


class CompanyMandate(TimeStampedModel):
    company = models.ForeignKey(
        "features.Company", on_delete=models.PROTECT, related_name="mandates"
    )
    membership = models.ForeignKey(
        "features.CompanyMembership", on_delete=models.PROTECT, related_name="mandates"
    )
    kind = models.CharField(
        max_length=8, choices=[("sign", "Signing"), ("pay", "Payment")]
    )
    state = models.CharField(max_length=12, default="pending")
    revision = models.PositiveIntegerField(default=1)
    membership_revision = models.PositiveIntegerField()
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    limit_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    evidence_reference = models.CharField(max_length=200)
    reason = models.TextField()
    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", null=True
    )
    reviewed_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(valid_until__gt=F("valid_from")),
                name="company_mandate_valid_interval",
            ),
            models.CheckConstraint(
                check=Q(limit_minor__gt=0), name="company_mandate_positive_limit"
            ),
        ]


class CompanyContractPreparation(TimeStampedModel):
    booking = models.OneToOneField(
        "features.CompanyBookingItem",
        on_delete=models.PROTECT,
        related_name="contract_preparation",
    )
    signer_mandate = models.ForeignKey(
        CompanyMandate, on_delete=models.PROTECT, related_name="signing_preparations"
    )
    payer_mandate = models.ForeignKey(
        CompanyMandate, on_delete=models.PROTECT, related_name="payment_preparations"
    )
    revision = models.PositiveIntegerField(default=1)
    state = models.CharField(max_length=24, default="awaiting_reviews")
    snapshot = models.JSONField()
    snapshot_digest = models.CharField(max_length=64)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )


class CompanyPreparationConsent(TimeStampedModel):
    preparation = models.ForeignKey(
        CompanyContractPreparation, on_delete=models.PROTECT, related_name="consents"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    role = models.CharField(max_length=12)
    snapshot_digest = models.CharField(max_length=64)
    decision = models.CharField(max_length=12)
    reason = models.TextField(blank=True)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["preparation", "actor", "role", "snapshot_digest"],
                name="company_preparation_consent_once",
            )
        ]
