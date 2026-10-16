"""Owner payments models with unchanged Django identities."""

import uuid
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from core_apps.common.models import TimeStampedModel


class RentalCommercialPolicy(TimeStampedModel):
    version = models.CharField(max_length=40, unique=True)
    commission_rate_bps = models.PositiveIntegerField(default=1000)
    commission_payer = models.CharField(max_length=20, default="owner")
    commission_basis = models.CharField(max_length=40, default="first_period_base_rent")
    processing_fee_payer = models.CharField(max_length=20, default="platform")
    renewal_commission_rate_bps = models.PositiveIntegerField(default=0)
    timezone = models.CharField(max_length=40, default="Africa/Cairo")
    billing_cycle = models.CharField(max_length=20, default="monthly")
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    summary = models.JSONField(default=dict)
    lifecycle_rules = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)


class OwnerPaymentProfile(TimeStampedModel):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        PENDING = "pending", "Pending"
        READY = "ready", "Ready"
        RESTRICTED = "restricted", "Restricted"

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_payment_profile",
    )
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NOT_STARTED
    )
    provider = models.CharField(max_length=40, default="")
    provider_account_id = models.CharField(max_length=120, blank=True, default="")
    masked_beneficiary = models.JSONField(default=dict, blank=True)
    requirements = models.JSONField(default=list, blank=True)
    accepted_policy_versions = models.JSONField(default=list, blank=True)
    payout_ready = models.BooleanField(default=False)


class OwnerOnboardingSession(TimeStampedModel):
    owner_profile = models.ForeignKey(
        OwnerPaymentProfile,
        on_delete=models.PROTECT,
        related_name="onboarding_sessions",
    )
    request_key = models.UUIDField()
    profile_revision = models.PositiveIntegerField()
    provider_session_id = models.CharField(max_length=120)
    hosted_url = models.URLField(max_length=500)
    status = models.CharField(max_length=20, default="created")
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner_profile", "request_key"],
                name="unique_owner_onboarding_request",
            )
        ]
