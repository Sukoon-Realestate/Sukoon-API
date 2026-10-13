"""Condition models with unchanged Django identities."""

import uuid
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from core_apps.common.models import TimeStampedModel
from .agreements import Lease
from .invoices import RentInvoice


class RentalEvidence(TimeStampedModel):
    class MalwareStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SAFE = "safe", "Safe"
        UNSAFE = "unsafe", "Unsafe"
        FAILED = "failed", "Failed"

    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="evidence")
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_evidence",
    )
    request_key = models.UUIDField()
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=80)
    size_bytes = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    storage_provider = models.CharField(max_length=40, default="fake")
    storage_key = models.CharField(max_length=255, unique=True)
    private_content = models.BinaryField(null=True, blank=True, editable=False)
    malware_status = models.CharField(
        max_length=20, choices=MalwareStatus.choices, default=MalwareStatus.PENDING
    )
    revision = models.PositiveIntegerField(default=1)
    retain_until = models.DateField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["uploader", "lease", "request_key"],
                name="unique_rental_evidence_request",
            )
        ]


class RentalHandover(TimeStampedModel):
    class Kind(models.TextChoices):
        MOVE_IN = "move_in", "Move in"
        MOVE_OUT = "move_out", "Move out"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_APPROVAL = "pending_approval", "Pending approval"
        ACCEPTED = "accepted", "Accepted"
        DISPUTED = "disputed", "Disputed"

    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="handovers")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.DRAFT
    )
    revision = models.PositiveIntegerField(default=1)
    possession_on = models.DateField()
    condition = models.JSONField(default=dict)
    keys = models.JSONField(default=dict)
    meters = models.JSONField(default=dict)
    inventory = models.JSONField(default=list)
    approvals = models.JSONField(default=list)
    evidence = models.ManyToManyField(
        RentalEvidence, related_name="handovers", blank=True
    )
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lease", "kind"], name="unique_lease_handover_kind"
            )
        ]


class DepositAgreement(TimeStampedModel):
    lease = models.OneToOneField(
        Lease, on_delete=models.PROTECT, related_name="deposit_agreement"
    )
    invoice = models.OneToOneField(
        RentInvoice,
        on_delete=models.PROTECT,
        related_name="deposit_agreement",
        null=True,
        blank=True,
    )
    revision = models.PositiveIntegerField(default=1)
    agreed_minor = models.PositiveBigIntegerField(default=0)
    due_minor = models.PositiveBigIntegerField(default=0)
    collected_minor = models.PositiveBigIntegerField(default=0)
    returned_minor = models.PositiveBigIntegerField(default=0)
    applied_minor = models.PositiveBigIntegerField(default=0)
    disputed_minor = models.PositiveBigIntegerField(default=0)
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
