"""Ledger models with unchanged Django identities."""

import uuid
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from core_apps.common.models import TimeStampedModel
from .invoices import BillingPeriod
from .agreements import Lease
from .payments import PaymentAttempt
from .invoices import RentInvoice


class LedgerTransaction(TimeStampedModel):
    reference = models.CharField(max_length=120, unique=True)
    kind = models.CharField(max_length=40)
    lease = models.ForeignKey(
        Lease,
        on_delete=models.PROTECT,
        related_name="ledger_transactions",
        null=True,
        blank=True,
    )
    invoice = models.ForeignKey(
        RentInvoice,
        on_delete=models.PROTECT,
        related_name="ledger_transactions",
        null=True,
        blank=True,
    )
    payment_attempt = models.ForeignKey(
        PaymentAttempt,
        on_delete=models.PROTECT,
        related_name="ledger_transactions",
        null=True,
        blank=True,
    )
    occurred_at = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)


class LedgerEntry(TimeStampedModel):
    class Direction(models.TextChoices):
        DEBIT = "debit", "Debit"
        CREDIT = "credit", "Credit"

    transaction = models.ForeignKey(
        LedgerTransaction, on_delete=models.PROTECT, related_name="entries"
    )
    account = models.CharField(max_length=60)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)


class OwnerPayable(TimeStampedModel):
    lease = models.ForeignKey(
        Lease, on_delete=models.PROTECT, related_name="owner_payables"
    )
    invoice = models.ForeignKey(
        RentInvoice, on_delete=models.PROTECT, related_name="owner_payables"
    )
    payment_attempt = models.OneToOneField(
        PaymentAttempt,
        on_delete=models.PROTECT,
        related_name="owner_payable",
        null=True,
        blank=True,
    )
    billing_period = models.ForeignKey(
        BillingPeriod,
        on_delete=models.PROTECT,
        related_name="owner_payables",
        null=True,
        blank=True,
    )
    source_reference = models.CharField(
        max_length=120, null=True, blank=True, unique=True
    )
    revision = models.PositiveIntegerField(default=1)
    gross_minor = models.PositiveBigIntegerField()
    commission_minor = models.PositiveBigIntegerField(default=0)
    processing_fee_minor = models.PositiveBigIntegerField(default=0)
    net_minor = models.PositiveBigIntegerField()
    settlement_status = models.CharField(max_length=20, default="pending")
    payout_status = models.CharField(max_length=24, default="pending_eligibility")
    blocking_reasons = models.JSONField(default=list, blank=True)


class PayoutBatch(TimeStampedModel):
    class Status(models.TextChoices):
        APPROVED = "approved", "Approved"
        PROCESSING = "processing", "Processing"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.APPROVED
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_payout_batches",
    )
    request_key = models.UUIDField(unique=True)
    provider_batch_id = models.CharField(max_length=120, blank=True, default="")
    revision = models.PositiveIntegerField(default=1)


class RentalPayout(TimeStampedModel):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        PROCESSING = "processing", "Processing"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        HELD = "held", "Held"

    batch = models.ForeignKey(
        PayoutBatch, on_delete=models.PROTECT, related_name="payouts"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_payouts",
    )
    lease = models.ForeignKey(Lease, on_delete=models.PROTECT, related_name="payouts")
    payables = models.ManyToManyField(OwnerPayable, related_name="payouts")
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    masked_beneficiary = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CREATED
    )
    provider_payout_id = models.CharField(max_length=120, blank=True, default="")
    hold_reason = models.CharField(max_length=255, blank=True, default="")
    failure_code = models.CharField(max_length=80, blank=True, default="")
    revision = models.PositiveIntegerField(default=1)


class PayoutAuditEvent(TimeStampedModel):
    payout = models.ForeignKey(
        RentalPayout, on_delete=models.PROTECT, related_name="audit_events"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payout_audit_events",
    )
    action = models.CharField(max_length=40)
    metadata = models.JSONField(default=dict, blank=True)
