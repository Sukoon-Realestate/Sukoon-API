"""Agreements models with unchanged Django identities."""

import uuid
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from core_apps.common.models import TimeStampedModel


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
        PENDING_SIGNATURES = "pending_signatures", "Pending signatures"
        PENDING = "pending", "Pending"
        SIGNED = "signed", "Signed"
        ACTIVE = "active", "Active"
        TERMINATION_PENDING = "termination_pending", "Termination pending"
        ENDED = "ended", "Ended"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    class OccupancyStatus(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        HANDOVER_PENDING = "handover_pending", "Handover pending"
        OCCUPIED = "occupied", "Occupied"
        MOVE_OUT_PENDING = "move_out_pending", "Move-out pending"
        RETURNED = "returned", "Returned"
        HANDOVER_DISPUTED = "handover_disputed", "Handover disputed"

    class FinancialClosureStatus(models.TextChoices):
        OPEN = "open", "Open"
        SETTLEMENT_PENDING = "settlement_pending", "Settlement pending"
        CLOSED = "closed", "Closed"
        REOPENED_FOR_ADJUSTMENT = (
            "reopened_for_adjustment",
            "Reopened for adjustment",
        )

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
    tenancy_root_id = models.UUIDField(
        default=uuid.uuid4, editable=False, db_index=True
    )
    occupancy_status = models.CharField(
        max_length=24,
        choices=OccupancyStatus.choices,
        default=OccupancyStatus.NOT_STARTED,
    )
    financial_closure_status = models.CharField(
        max_length=32,
        choices=FinancialClosureStatus.choices,
        default=FinancialClosureStatus.OPEN,
    )
    legacy_read_only = models.BooleanField(default=True)
    terms = models.JSONField(default=dict, blank=True)
    policy_version = models.CharField(max_length=40, blank=True, default="")
    reviewed_by = models.JSONField(default=list, blank=True)
    document_id = models.UUIDField(null=True, blank=True)
    document_hash = models.CharField(max_length=64, blank=True, default="")
    hold_expires_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "offer_id"],
                condition=Q(
                    legacy_read_only=True,
                    status__in=[
                        "draft",
                        "pending_signatures",
                        "pending",
                        "signed",
                        "active",
                        "termination_pending",
                    ],
                ),
                name="unique_live_lease_per_accommodation",
            )
        ]


class SigningSession(TimeStampedModel):
    lease = models.ForeignKey(
        Lease, on_delete=models.CASCADE, related_name="signing_sessions"
    )
    signer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default="pending")
    hosted_url = models.URLField(max_length=500)
    expires_at = models.DateTimeField()
    request_key = models.UUIDField(null=True, blank=True)
    lease_revision = models.PositiveIntegerField(default=1)
    document_id = models.UUIDField(null=True, blank=True)
    document_hash = models.CharField(max_length=64, blank=True, default="")
    provider_session_id = models.CharField(max_length=120, blank=True, default="")
    completed_at = models.DateTimeField(null=True, blank=True)
