from django.conf import settings
from django.db import models

from core_apps.common.models import TimeStampedModel


class IdempotencyRecord(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    operation = models.CharField(max_length=80)
    request_key = models.CharField(max_length=100)
    fingerprint = models.CharField(max_length=64)
    response_data = models.JSONField(default=dict)
    response_status = models.PositiveSmallIntegerField(default=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "operation", "request_key"],
                name="unique_feature_request_key",
            )
        ]


class BoostCampaign(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"
        FAILED = "failed", "Failed"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="boost_campaigns",
    )
    property = models.ForeignKey(
        "properties.Property", on_delete=models.CASCADE, related_name="boost_campaigns"
    )
    option_id = models.CharField(max_length=50)
    duration_days = models.PositiveSmallIntegerField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    impressions = models.PositiveIntegerField(null=True, blank=True)


class SearchAlert(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="search_alerts"
    )
    name = models.CharField(max_length=150)
    cadence = models.CharField(
        max_length=20, choices=[("instant", "Instant"), ("daily", "Daily")]
    )
    filters = models.JSONField(default=dict)
    enabled = models.BooleanField(default=True)
    revision = models.PositiveIntegerField(default=1)
    last_matched_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)


class ListingSuggestion(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listing_suggestions",
    )
    property = models.ForeignKey(
        "properties.Property", on_delete=models.CASCADE, null=True, blank=True
    )
    language = models.CharField(max_length=2)
    facts = models.JSONField(default=dict)
    suggested_title = models.CharField(max_length=150)
    suggested_description = models.TextField(max_length=5000)
    warnings = models.JSONField(default=list)


class LeaseEligibleTenant(TimeStampedModel):
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="lease_eligible_tenants",
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lease_eligibilities",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_lease_eligibilities",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["property", "tenant"], name="unique_property_lease_tenant"
            )
        ]


class Lease(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        SIGNED = "signed", "Signed"
        ACTIVE = "active", "Active"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    property = models.ForeignKey(
        "properties.Property", on_delete=models.PROTECT, related_name="digital_leases"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_digital_leases",
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tenant_digital_leases",
    )
    template_id = models.CharField(max_length=80)
    template_version = models.CharField(max_length=40)
    start_date = models.DateField()
    end_date = models.DateField()
    rent_amount_minor = models.PositiveBigIntegerField()
    rent_currency = models.CharField(max_length=3, default="EGP")
    rent_exponent = models.PositiveSmallIntegerField(default=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    revision = models.PositiveIntegerField(default=1)
    document_url = models.URLField(max_length=500, blank=True, default="")
    offer_id = models.CharField(max_length=64, blank=True, default="")
    offer_snapshot = models.JSONField(null=True, blank=True)


class SigningSession(TimeStampedModel):
    lease = models.ForeignKey(
        Lease, on_delete=models.CASCADE, related_name="signing_sessions"
    )
    signer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default="pending")
    hosted_url = models.URLField(max_length=500)
    expires_at = models.DateTimeField()


class RentInvoice(TimeStampedModel):
    class Status(models.TextChoices):
        DUE = "due", "Due"
        OVERDUE = "overdue", "Overdue"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="invoices")
    reference = models.CharField(max_length=50, unique=True)
    due_date = models.DateField()
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DUE)
    receipt_url = models.URLField(max_length=500, blank=True, default="")


class CheckoutSession(TimeStampedModel):
    invoice = models.ForeignKey(
        RentInvoice, on_delete=models.CASCADE, related_name="checkout_sessions"
    )
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default="pending")
    hosted_url = models.URLField(max_length=500)
    expires_at = models.DateTimeField()
