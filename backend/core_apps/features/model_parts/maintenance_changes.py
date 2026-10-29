"""Maintenance changes models with unchanged Django identities."""

import uuid
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from core_apps.common.models import TimeStampedModel
from .agreements import Lease
from .invoices import RentInvoice
from .condition import RentalEvidence


class MaintenanceRequest(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        APPOINTMENT_PROPOSED = "appointment_proposed", "Appointment proposed"
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In progress"
        RESOLUTION_REPORTED = "resolution_reported", "Resolution reported"
        RESOLVED = "resolved", "Resolved"
        CANCELLED = "cancelled", "Cancelled"

    lease = models.ForeignKey(
        Lease, on_delete=models.PROTECT, related_name="maintenance_requests"
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reported_maintenance",
    )
    revision = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=160)
    description = models.TextField()
    category = models.CharField(max_length=40)
    priority = models.CharField(max_length=20)
    access_times = models.JSONField(default=list)
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.OPEN
    )
    appointment_at = models.DateTimeField(null=True, blank=True)
    appointment_ends_at = models.DateTimeField(null=True, blank=True)
    appointment_version = models.PositiveIntegerField(default=0)
    access_approved_version = models.PositiveIntegerField(null=True, blank=True)
    proposed_cost_minor = models.PositiveBigIntegerField(null=True, blank=True)
    cost_version = models.PositiveIntegerField(default=0)
    approved_cost_version = models.PositiveIntegerField(null=True, blank=True)
    cost_payer = models.CharField(max_length=10, blank=True, default="")
    evidence = models.ManyToManyField(
        RentalEvidence, related_name="maintenance_requests", blank=True
    )


class MaintenanceEvent(TimeStampedModel):
    maintenance_request = models.ForeignKey(
        MaintenanceRequest, on_delete=models.PROTECT, related_name="events"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="maintenance_events",
    )
    action = models.CharField(max_length=40)
    note = models.TextField(blank=True, default="")
    appointment_at = models.DateTimeField(null=True, blank=True)
    cost_minor = models.PositiveBigIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)


class RentalChange(TimeStampedModel):
    class Kind(models.TextChoices):
        PAYMENT_EXTENSION = "payment_extension", "Payment extension"
        AMENDMENT = "amendment", "Amendment"
        RENEWAL = "renewal", "Renewal"
        TERMINATION = "termination", "Termination"
        EXTERNAL_PAYMENT = "external_payment", "External payment"

    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        CHANGES_REQUESTED = "changes_requested", "Changes requested"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        PENDING_SIGNATURES = "pending_signatures", "Pending signatures"
        SIGNED = "signed", "Signed"
        APPLIED = "applied", "Applied"
        REVIEW_REQUIRED = "review_required", "Operations review required"

    lease = models.ForeignKey(
        Lease, on_delete=models.PROTECT, related_name="rental_changes"
    )
    result_lease = models.OneToOneField(
        Lease,
        on_delete=models.PROTECT,
        related_name="source_rental_change",
        null=True,
        blank=True,
    )
    invoice = models.ForeignKey(
        RentInvoice,
        on_delete=models.PROTECT,
        related_name="rental_changes",
        null=True,
        blank=True,
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_rental_changes",
    )
    kind = models.CharField(max_length=30, choices=Kind.choices)
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.PROPOSED
    )
    revision = models.PositiveIntegerField(default=1)
    reason = models.TextField(blank=True, default="")
    requested_date = models.DateField(null=True, blank=True)
    original_due_at = models.DateTimeField(null=True, blank=True)
    deferred_until = models.DateTimeField(null=True, blank=True)
    effective_on = models.DateField(null=True, blank=True)
    amount_minor = models.PositiveBigIntegerField(null=True, blank=True)
    method = models.CharField(max_length=40, blank=True, default="")
    terms = models.JSONField(default=dict, blank=True)
    previous_terms = models.JSONField(default=dict, blank=True)
    termination_notice_snapshot = models.JSONField(default=dict, blank=True)
    approvals = models.JSONField(default=list, blank=True)
    evidence = models.ManyToManyField(
        RentalEvidence, related_name="rental_changes", blank=True
    )
    document_id = models.UUIDField(null=True, blank=True)
    document_hash = models.CharField(max_length=64, blank=True, default="")
    signed_by = models.JSONField(default=list, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    content_revision = models.PositiveIntegerField(default=1)


class RentalChangeVersion(TimeStampedModel):
    change = models.ForeignKey(RentalChange, on_delete=models.PROTECT, related_name="versions")
    version = models.PositiveIntegerField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    lease_revision = models.PositiveIntegerField()
    snapshot = models.JSONField()
    baseline = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["change", "version"], name="rental_change_content_version")]


class ChangeSigningSession(TimeStampedModel):
    change = models.ForeignKey(
        RentalChange, on_delete=models.PROTECT, related_name="signing_sessions"
    )
    signer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_change_signing_sessions",
    )
    request_key = models.UUIDField()
    change_revision = models.PositiveIntegerField()
    document_id = models.UUIDField()
    document_hash = models.CharField(max_length=64)
    provider_session_id = models.CharField(max_length=120, unique=True)
    hosted_url = models.URLField(max_length=500)
    status = models.CharField(max_length=20, default="pending")
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["change", "signer", "request_key"],
                name="unique_change_signing_request",
            )
        ]
