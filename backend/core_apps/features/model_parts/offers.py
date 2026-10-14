"""Offers models with unchanged Django identities."""

import uuid
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from core_apps.common.models import TimeStampedModel
from .agreements import Lease


class RentalInterest(TimeStampedModel):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under review"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"
        PROPOSED = "proposed", "Proposed"
        INVITED = "invited", "Invited"

    property = models.ForeignKey(
        "properties.Property", on_delete=models.PROTECT, related_name="rental_interests"
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_interests",
    )
    offer_id = models.CharField(max_length=64)
    offer_revision = models.PositiveIntegerField()
    offer_snapshot = models.JSONField()
    desired_start = models.DateField()
    months = models.PositiveSmallIntegerField()
    occupants = models.PositiveSmallIntegerField(default=1)
    message = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SUBMITTED
    )
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                check=Q(revision__gte=1), name="rental_interest_revision_positive"
            ),
            models.CheckConstraint(
                check=Q(months__gte=1), name="rental_interest_months_positive"
            ),
        ]


class TermsProposal(TimeStampedModel):
    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        CHANGES_REQUESTED = "changes_requested", "Changes requested"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        SUPERSEDED = "superseded", "Superseded"

    interest = models.ForeignKey(
        RentalInterest, on_delete=models.PROTECT, related_name="terms_proposals"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_terms_proposals",
    )
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.PROPOSED
    )
    terms = models.JSONField()
    previous_terms = models.JSONField(default=list, blank=True)
    offer_snapshot = models.JSONField()
    accepted_by = models.JSONField(default=list, blank=True)


class TenancyInvitation(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        REVOKED = "revoked", "Revoked"
        EXPIRED = "expired", "Expired"

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        related_name="tenancy_invitations",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_tenancy_invitations",
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_tenancy_invitations",
    )
    offer_id = models.CharField(max_length=64, blank=True, default="")
    offer_snapshot = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    revision = models.PositiveIntegerField(default=1)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="initiated_tenancy_invitations",
    )
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="responded_tenancy_invitations",
        null=True,
        blank=True,
    )
    lease = models.OneToOneField(
        Lease,
        on_delete=models.PROTECT,
        related_name="tenancy_invitation",
        null=True,
        blank=True,
    )
    interest = models.ForeignKey(
        "RentalInterest",
        on_delete=models.PROTECT,
        related_name="invitations",
        null=True,
        blank=True,
    )
    terms_proposal = models.ForeignKey(
        "TermsProposal",
        on_delete=models.PROTECT,
        related_name="invitations",
        null=True,
        blank=True,
    )
    eligibility_snapshot = models.JSONField(default=dict, blank=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    provenance_version = models.CharField(max_length=30, default="visit_decision_v1")
    source_visit = models.ForeignKey(
        "properties.PropertyVisit",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="rental_invitations",
    )
    source_decision = models.ForeignKey(
        "properties.PropertyVisitDecision",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="rental_invitations",
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["owner", "-created_at"], name="invite_owner_created_idx"
            ),
            models.Index(
                fields=["tenant", "-created_at"], name="invite_tenant_created_idx"
            ),
            models.Index(
                fields=["property", "offer_id", "status"],
                name="invite_eligibility_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=~Q(owner=F("tenant")), name="invitation_participants_distinct"
            ),
            models.CheckConstraint(
                check=Q(revision__gte=1), name="invitation_revision_positive"
            ),
            models.UniqueConstraint(
                fields=["owner", "property", "tenant", "offer_id"],
                condition=Q(status__in=["pending", "accepted"], lease__isnull=True),
                name="unique_live_tenancy_invitation",
            ),
            models.UniqueConstraint(
                fields=["source_visit"],
                condition=Q(status__in=["pending", "accepted"], lease__isnull=True),
                name="unique_live_visit_invitation",
            ),
        ]
