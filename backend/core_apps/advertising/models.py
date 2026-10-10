from django.conf import settings
from django.db import models

from core_apps.common.models import TimeStampedModel


class AdvertisingPlan(models.Model):
    class DurationUnit(models.TextChoices):
        WEEK = "week", "Week"
        CALENDAR_MONTH = "calendar_month", "Calendar month"
        CALENDAR_YEAR = "calendar_year", "Calendar year"

    id = models.CharField(primary_key=True, max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title_en = models.CharField(max_length=100)
    title_ar = models.CharField(max_length=100)
    duration_unit = models.CharField(max_length=20, choices=DurationUnit.choices)
    duration_count = models.PositiveSmallIntegerField(default=1)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    revision = models.CharField(max_length=32, default="1")
    active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title_en


class AdvertisementOperation(TimeStampedModel):
    class State(models.TextChoices):
        PROCESSING = "processing", "Processing"
        FOUND = "found", "Found"
        REJECTED = "rejected", "Rejected"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="advertisement_operations",
    )
    operation_id = models.CharField(max_length=128)
    state = models.CharField(max_length=20, choices=State.choices)
    payload_fingerprint = models.CharField(max_length=64, blank=True, default="")
    retry_allowed = models.BooleanField(default=False)
    rejection_errors = models.JSONField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "operation_id"],
                name="unique_ad_operation_per_owner",
            )
        ]


class Advertisement(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"

    PLACEMENT_TENANT_HOME = "tenant_home"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="advertisements",
    )
    operation = models.OneToOneField(
        AdvertisementOperation,
        on_delete=models.PROTECT,
        related_name="advertisement",
    )
    title = models.CharField(max_length=150)
    description = models.CharField(max_length=500, blank=True, default="")
    placement = models.CharField(max_length=40, default=PLACEMENT_TENANT_HOME)
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        related_name="advertisements",
        null=True,
        blank=True,
    )
    offer_id = models.CharField(max_length=64, blank=True, default="")
    plan_snapshot = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        db_index=True,
    )
    starts_at = models.DateTimeField(null=True, blank=True, db_index=True)
    ends_at = models.DateTimeField(null=True, blank=True, db_index=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["placement", "status", "starts_at", "ends_at"],
                name="advertising_public_feed_idx",
            )
        ]


class AdvertisementMedia(TimeStampedModel):
    advertisement = models.OneToOneField(
        Advertisement,
        on_delete=models.CASCADE,
        related_name="media",
    )
    banner = models.FileField(upload_to="advertising/banner_ads/%Y/%m/")
    sha256 = models.CharField(max_length=64)
    content_type = models.CharField(max_length=32)
    size_bytes = models.PositiveBigIntegerField()


class MockAdvertisementPayment(TimeStampedModel):
    STATUS_SUCCEEDED = "mock_succeeded"
    MODE_MOCK = "mock"

    advertisement = models.OneToOneField(
        Advertisement,
        on_delete=models.PROTECT,
        related_name="payment",
    )
    operation_id = models.CharField(max_length=160)
    payment_mode = models.CharField(max_length=20, default=MODE_MOCK)
    status = models.CharField(max_length=30, default=STATUS_SUCCEEDED)

    def __str__(self):
        return f"Mock payment for {self.advertisement_id}"
