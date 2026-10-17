"""Confirmed experience facts attached to canonical leases and assignments.

These records never activate a lease, transfer money, or infer possession from
planned dates. They retain the parties' confirmations for reputation reads.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q, F
from core_apps.common.models import TimeStampedModel


class CompanyLeaseBinding(TimeStampedModel):
    lease = models.OneToOneField(
        "features.Lease", on_delete=models.PROTECT, related_name="company_binding"
    )
    booking = models.OneToOneField(
        "features.CompanyBookingItem",
        on_delete=models.PROTECT,
        null=True,
        related_name="confirmed_lease_binding",
    )
    renter_company = models.ForeignKey(
        "features.Company",
        on_delete=models.PROTECT,
        null=True,
        related_name="rental_bindings",
    )
    landlord_company = models.ForeignKey(
        "features.Company",
        on_delete=models.PROTECT,
        null=True,
        related_name="letting_bindings",
    )
    proposed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    state = models.CharField(max_length=16, default="pending")
    revision = models.PositiveIntegerField(default=1)
    source_snapshot = models.JSONField(default=dict)
    approvals = models.JSONField(default=dict)
    accepted_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(renter_company__isnull=False)
                | Q(landlord_company__isnull=False),
                name="binding_has_company_party",
            ),
            models.CheckConstraint(
                check=Q(renter_company__isnull=True)
                | Q(landlord_company__isnull=True)
                | ~Q(renter_company=F("landlord_company")),
                name="binding_distinct_companies",
            ),
        ]


class CompanyReviewAuthority(TimeStampedModel):
    binding = models.ForeignKey(
        CompanyLeaseBinding, on_delete=models.PROTECT, related_name="review_authorities"
    )
    membership = models.ForeignKey(
        "features.CompanyMembership", on_delete=models.PROTECT
    )
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    can_submit = models.BooleanField(default=False)
    can_view_reputation = models.BooleanField(default=False)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["binding", "membership"], name="company_review_authority_once"
            )
        ]


class EmployeeOccupancyConfirmation(TimeStampedModel):
    assignment = models.ForeignKey(
        "features.EmployeeAssignment",
        on_delete=models.PROTECT,
        related_name="occupancy_confirmations",
    )
    kind = models.CharField(
        max_length=12, choices=[("arrival", "Arrival"), ("departure", "Departure")]
    )
    possession_on = models.DateField()
    proposed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    state = models.CharField(max_length=16, default="pending")
    revision = models.PositiveIntegerField(default=1)
    assignment_revision = models.PositiveIntegerField()
    approvals = models.JSONField(default=dict)
    source_snapshot = models.JSONField(default=dict)
    accepted_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "kind"], name="assignment_occupancy_phase_once"
            )
        ]


class LeaseResponsibilityTransition(TimeStampedModel):
    lease = models.ForeignKey(
        "features.Lease",
        on_delete=models.PROTECT,
        related_name="responsibility_transitions",
    )
    tenancy_root_id = models.UUIDField(db_index=True)
    previous_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="responsibility_transitions_from",
    )
    next_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="responsibility_transitions_to",
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="responsibility_transition_tenants",
    )
    effective_on = models.DateField()
    evidence = models.ForeignKey("features.RentalEvidence", on_delete=models.PROTECT)
    state = models.CharField(max_length=16, default="pending")
    revision = models.PositiveIntegerField(default=1)
    approvals = models.JSONField(default=dict)
    source_snapshot = models.JSONField(default=dict)
    accepted_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenancy_root_id", "effective_on"],
                name="responsibility_boundary_once",
            ),
            models.CheckConstraint(
                check=~Q(previous_owner=F("next_owner")),
                name="responsibility_changes_owner",
            ),
        ]
