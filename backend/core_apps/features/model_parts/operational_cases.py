"""Auditable operations over existing rental resources, never operator consent."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class RentalOperationalCase(TimeStampedModel):
    source_key = models.CharField(max_length=180, unique=True)
    kind = models.CharField(max_length=40)
    severity = models.CharField(max_length=20, default="normal")
    status = models.CharField(max_length=24, default="open")
    property = models.ForeignKey(
        "properties.Property", on_delete=models.PROTECT, null=True, blank=True
    )
    lease = models.ForeignKey(
        "Lease",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="operational_cases",
    )
    hold = models.ForeignKey(
        "ReservationHold",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="operational_cases",
    )
    payment_attempt = models.ForeignKey(
        "PaymentAttempt",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="operational_cases",
    )
    refund = models.ForeignKey(
        "RefundRequest", on_delete=models.PROTECT, null=True, blank=True
    )
    payout = models.ForeignKey(
        "RentalPayout", on_delete=models.PROTECT, null=True, blank=True
    )
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="opened_rental_cases",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assigned_rental_cases",
    )
    team = models.CharField(max_length=40, default="support")
    next_action = models.CharField(max_length=240)
    due_at = models.DateTimeField()
    escalated_at = models.DateTimeField(null=True, blank=True)
    reason = models.TextField()
    baseline = models.JSONField(default=dict)
    resolution_code = models.CharField(max_length=60, blank=True, default="")
    resolution = models.TextField(blank=True, default="")
    evidence = models.ManyToManyField(
        "RentalEvidence", blank=True, related_name="operational_cases"
    )
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        indexes = [
            models.Index(fields=["status", "due_at"], name="rental_case_queue_idx")
        ]


class RentalAuditEvent(TimeStampedModel):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    subject_kind = models.CharField(max_length=50)
    subject_id = models.UUIDField()
    subject_revision = models.PositiveIntegerField()
    action = models.CharField(max_length=60)
    reason = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict)


class RentalProviderInstruction(TimeStampedModel):
    """Durable identities survive a crash after an external instruction executes."""

    reference = models.CharField(max_length=160, unique=True)
    kind = models.CharField(max_length=30)
    provider = models.CharField(max_length=40)
    subject_id = models.UUIDField()
    subject_revision = models.PositiveIntegerField()
    status = models.CharField(max_length=24, default="pending")
    provider_reference = models.CharField(max_length=160, blank=True, default="")
    attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    failure_code = models.CharField(max_length=80, blank=True, default="")
    request_fingerprint = models.CharField(max_length=64)
    result = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "next_attempt_at"], name="rental_provider_retry_idx"
            )
        ]
