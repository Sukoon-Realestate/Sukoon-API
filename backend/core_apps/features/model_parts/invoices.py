"""Invoices models with unchanged Django identities."""

import uuid
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from core_apps.common.models import TimeStampedModel
from .agreements import Lease


class BillingPeriod(TimeStampedModel):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        ISSUED = "issued", "Issued"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    lease = models.ForeignKey(
        Lease, on_delete=models.PROTECT, related_name="billing_periods"
    )
    sequence = models.PositiveIntegerField()
    start = models.DateField()
    end_exclusive = models.DateField()
    issue_at = models.DateTimeField()
    due_at = models.DateTimeField()
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )

    class Meta:
        ordering = ["start", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["lease", "sequence"], name="unique_lease_billing_sequence"
            ),
            models.UniqueConstraint(
                fields=["lease", "start", "end_exclusive"],
                name="unique_lease_billing_period",
            ),
        ]


class RentInvoice(TimeStampedModel):
    class InvoiceType(models.TextChoices):
        RENT = "rent", "Rent"
        DEPOSIT = "deposit", "Deposit"
        ADJUSTMENT = "adjustment", "Adjustment"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        DUE = "due", "Due"
        OVERDUE = "overdue", "Overdue"
        PARTIALLY_PAID = "partially_paid", "Partially paid"
        PAID = "paid", "Paid"
        SETTLED = "settled", "Settled"
        CANCELLED = "cancelled", "Cancelled"
        WRITTEN_OFF = "written_off", "Written off"

    lease = models.ForeignKey(
        Lease, on_delete=models.PROTECT, related_name="invoices", null=True, blank=True
    )
    purpose = models.CharField(
        max_length=20,
        default="rent",
        choices=[
            ("rent", "Rent"),
            ("subscription", "Subscription"),
            ("advertising", "Advertising"),
            ("maintenance", "Maintenance"),
            ("promotion", "Promotion"),
            ("settlement", "Settlement"),
            ("adjustment", "Adjustment"),
            ("deposit", "Deposit"),
        ],
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="purchase_invoices",
    )
    workspace = models.CharField(max_length=10, default="tenant")
    organization = models.ForeignKey("features.Company", on_delete=models.PROTECT, null=True, blank=True)
    business_reference = models.CharField(max_length=100, blank=True, default="")
    purchase_snapshot = models.JSONField(default=dict, blank=True)
    reference = models.CharField(max_length=50, unique=True)
    due_date = models.DateField()
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DUE)
    receipt_url = models.URLField(max_length=500, blank=True, default="")
    revision = models.PositiveIntegerField(default=1)
    invoice_type = models.CharField(
        max_length=20, choices=InvoiceType.choices, default=InvoiceType.RENT
    )
    billing_period = models.OneToOneField(
        BillingPeriod,
        on_delete=models.PROTECT,
        related_name="invoice",
        null=True,
        blank=True,
    )
    period_start = models.DateField(null=True, blank=True)
    period_end_exclusive = models.DateField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    deferred_until = models.DateTimeField(null=True, blank=True)
    charges_minor = models.PositiveBigIntegerField(default=0)
    credits_minor = models.PositiveBigIntegerField(default=0)
    applied_minor = models.PositiveBigIntegerField(default=0)
    receipt_id = models.UUIDField(null=True, blank=True)
    beneficiary = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="beneficiary_invoices",
    )

    def save(self, *args, **kwargs):
        # Freeze the creditor when the obligation is first issued. A later
        # ownership transition must never redirect an existing receivable.
        if self._state.adding and self.lease_id and not self.beneficiary_id:
            self.beneficiary_id = self.lease.owner_id
        return super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(purpose="rent", lease__isnull=False)
                    | (
                        Q(
                            purpose__in=["subscription", "advertising", "maintenance", "promotion", "settlement", "adjustment", "deposit"],
                            lease__isnull=True,
                            payer__isnull=False,
                        )
                        & ~Q(business_reference="")
                    )
                ),
                name="invoice_purpose_has_subject",
            ),
            models.UniqueConstraint(
                fields=["purpose", "business_reference"],
                condition=~Q(purpose="rent"),
                name="unique_purchase_invoice_subject",
            ),
        ]


class InvoiceLine(TimeStampedModel):
    invoice = models.ForeignKey(
        RentInvoice, on_delete=models.PROTECT, related_name="lines"
    )
    line_type = models.CharField(max_length=40)
    description = models.CharField(max_length=255)
    amount_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    source = models.JSONField(default=dict, blank=True)


class PaymentQuote(TimeStampedModel):
    invoice = models.ForeignKey(
        RentInvoice, on_delete=models.PROTECT, related_name="payment_quotes"
    )
    request_key = models.UUIDField()
    invoice_revision = models.PositiveIntegerField()
    payer_amount_minor = models.PositiveBigIntegerField()
    tenant_service_fee_minor = models.PositiveBigIntegerField(default=0)
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    purchase_route = models.JSONField(default=dict, blank=True)
    policy_version = models.CharField(max_length=40)
    fingerprint = models.CharField(max_length=64)
    expires_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["invoice", "request_key"], name="unique_invoice_quote_request"
            )
        ]
