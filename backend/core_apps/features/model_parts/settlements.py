"""Settlements models with unchanged Django identities."""

import uuid
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from core_apps.common.models import TimeStampedModel
from .agreements import Lease
from .payments import PaymentAttempt
from .condition import RentalEvidence


class FinalSettlement(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PROPOSED = "proposed", "Proposed"
        ACCEPTED = "accepted", "Accepted"
        DISPUTED = "disputed", "Disputed"

    lease = models.OneToOneField(
        Lease, on_delete=models.PROTECT, related_name="final_settlement"
    )
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    lines = models.JSONField(default=list)
    rent_balance_minor = models.BigIntegerField(default=0)
    deposit_to_return_minor = models.BigIntegerField(default=0)
    refund_due_minor = models.BigIntegerField(default=0)
    total_due_minor = models.BigIntegerField(default=0)
    accepted_by = models.JSONField(default=list)
    disputed_item_ids = models.JSONField(default=list)
    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="proposed_settlements",
        null=True,
    )
    financial_snapshot = models.JSONField(default=dict, blank=True)
    execution_plan = models.JSONField(default=dict, blank=True)
    execution_status = models.CharField(max_length=20, default="not_started")
    executed_at = models.DateTimeField(null=True, blank=True)
    history = models.JSONField(default=list, blank=True)


class RefundRequest(TimeStampedModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        PROCESSING = "processing", "Processing"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        REJECTED = "rejected", "Rejected"

    lease = models.ForeignKey(
        Lease, on_delete=models.PROTECT, related_name="refund_requests"
    )
    payment_attempt = models.ForeignKey(
        PaymentAttempt, on_delete=models.PROTECT, related_name="refund_requests"
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_refund_requests",
    )
    revision = models.PositiveIntegerField(default=1)
    amount_minor = models.PositiveBigIntegerField()
    refundable_balance_snapshot_minor = models.PositiveBigIntegerField()
    reason = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.REQUESTED
    )
    provider_refund_id = models.CharField(max_length=120, blank=True, default="")
    failure_code = models.CharField(max_length=80, blank=True, default="")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_refunds",
        null=True,
        blank=True,
    )
    request_key = models.UUIDField()
    allocations = models.JSONField(default=dict, blank=True)
    purpose = models.CharField(max_length=30, default="payment_reversal")
    commission_reversal_minor = models.PositiveBigIntegerField(default=0)
    owner_recovery_minor = models.PositiveBigIntegerField(default=0)
    owner_recovered_minor = models.PositiveBigIntegerField(default=0)
    recovery_reference = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["requester", "payment_attempt", "request_key"],
                name="unique_refund_request_key",
            )
        ]


class RentalDispute(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"
        REJECTED = "rejected", "Rejected"

    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="disputes")
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="opened_rental_disputes",
    )
    subject_kind = models.CharField(max_length=40)
    subject_id = models.UUIDField()
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    reason = models.TextField()
    resolution = models.TextField(blank=True, default="")
    responses = models.JSONField(default=list)
    evidence = models.ManyToManyField(
        RentalEvidence, related_name="disputes", blank=True
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="resolved_rental_disputes",
        null=True,
        blank=True,
    )


from .documents import RentalDocument, RentalReview, PrivateAccessRevocation
