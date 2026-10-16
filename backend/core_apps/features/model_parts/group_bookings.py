"""Booking coordination references existing planning, agreements and payments."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from core_apps.common.models import TimeStampedModel


class GroupBookingProposal(TimeStampedModel):
    application = models.ForeignKey(
        "GroupProcess", on_delete=models.PROTECT, related_name="booking_proposals"
    )
    group = models.ForeignKey(
        "HousingGroup", on_delete=models.PROTECT, related_name="booking_proposals"
    )
    property = models.ForeignKey("properties.Property", on_delete=models.PROTECT)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="group_booking_proposals",
    )
    booking_model = models.CharField(
        max_length=24,
        choices=[
            ("independent", "Independent"),
            ("conditional_bundle", "Conditional bundle"),
        ],
    )
    status = models.CharField(max_length=30, default="draft")
    revision = models.PositiveIntegerField(default=1)
    roster_revision = models.PositiveIntegerField()
    allocation_revision = models.PositiveIntegerField(default=1)
    terms_revision = models.PositiveIntegerField(default=1)
    terms_digest = models.CharField(max_length=64)
    policy_version = models.CharField(max_length=40)
    starts_on = models.DateField()
    ends_on_exclusive = models.DateField()
    deadline = models.DateTimeField()
    total_rent_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    incomplete_policy = models.CharField(
        max_length=40, default="preserve_independent_agreements"
    )
    committed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["application"],
                condition=Q(status__in=["draft", "submitted", "awaiting_participants"]),
                name="unique_live_group_booking",
            )
        ]


class GroupBookingParticipant(TimeStampedModel):
    proposal = models.ForeignKey(
        GroupBookingProposal, on_delete=models.PROTECT, related_name="participants"
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="group_booking_participations",
    )
    offer_id = models.CharField(max_length=64)
    offer_revision = models.PositiveIntegerField()
    selection_snapshot = models.JSONField()
    rent_amount_minor = models.PositiveBigIntegerField()
    terms = models.JSONField(default=dict)
    consent_status = models.CharField(max_length=20, default="pending")
    consent_revision = models.PositiveIntegerField(null=True, blank=True)
    invitation = models.OneToOneField(
        "TenancyInvitation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="group_booking_participant",
    )
    lease = models.OneToOneField(
        "Lease",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="group_booking_participant",
    )
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["proposal", "tenant"], name="unique_group_booking_participant"
            )
        ]
