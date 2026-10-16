"""Planning models: roommate connection."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from core_apps.common.models import TimeStampedModel


class LifestyleProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lifestyle_profile",
    )
    revision = models.PositiveIntegerField(default=1)
    discoverable = models.BooleanField(default=False)
    habits = models.JSONField(default=dict)
    preferences = models.JSONField(default=dict)
    disclosed = models.JSONField(default=list)
    importance = models.JSONField(default=dict)
    details = models.JSONField(default=dict)
    search_context = models.JSONField(default=dict)
    reason_categories = models.JSONField(default=list)


class RoommateConnection(TimeStampedModel):
    first = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="first_roommate_connections",
    )
    second = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="second_roommate_connections",
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requested_roommate_connections",
    )
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, default="pending")
    note = models.TextField(blank=True, default="")
    blocked_by = models.JSONField(default=list)
    disclosure_grants = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["first", "second"], name="unique_roommate_pair"
            ),
            models.CheckConstraint(
                check=Q(first__lt=models.F("second")), name="ordered_roommate_pair"
            ),
        ]


class HousingGroup(TimeStampedModel):
    name = models.CharField(max_length=160)
    status = models.CharField(max_length=20, default="active")
    visibility = models.CharField(max_length=20, default="invite_only")
    revision = models.PositiveIntegerField(default=1)
    roster_revision = models.PositiveIntegerField(default=1)
    capacity = models.PositiveSmallIntegerField(default=2)
    criteria = models.JSONField(default=dict)
    shortlist = models.JSONField(default=list)
    proposals = models.JSONField(default=list)


class GroupMembership(TimeStampedModel):
    group = models.ForeignKey(
        HousingGroup, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="housing_memberships",
    )
    role = models.CharField(max_length=20, default="member")
    status = models.CharField(max_length=20, default="active")
    joined_revision = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["group", "user"], name="unique_housing_group_member"
            ),
            models.UniqueConstraint(
                fields=["group"],
                condition=Q(role="admin", status="active"),
                name="one_active_housing_group_admin",
            ),
        ]


class GroupInvitation(TimeStampedModel):
    group = models.ForeignKey(
        HousingGroup, on_delete=models.CASCADE, related_name="invitations"
    )
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, default="active")
    nonce = models.CharField(max_length=64)
    expires_at = models.DateTimeField()


class GroupProcess(TimeStampedModel):
    academic_plan = models.ForeignKey(
        "features.AcademicHousingPlan", on_delete=models.PROTECT, null=True, blank=True
    )
    academic_revision = models.PositiveIntegerField(null=True, blank=True)
    academic_snapshot = models.JSONField(default=dict)
    group = models.ForeignKey(
        HousingGroup, on_delete=models.PROTECT, related_name="processes"
    )
    initiated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    property = models.ForeignKey("properties.Property", on_delete=models.PROTECT)
    kind = models.CharField(max_length=20)
    revision = models.PositiveIntegerField(default=1)
    roster_revision = models.PositiveIntegerField()
    status = models.CharField(max_length=24, default="collecting_consent")
    selection = models.JSONField(default=dict)
    participant_ids = models.JSONField(default=list)
    consented_ids = models.JSONField(default=list)
    proposal_snapshot = models.JSONField(default=dict)
    owner_note = models.TextField(blank=True, default="")
    history = models.JSONField(default=list)
    appointment_at = models.DateTimeField(null=True, blank=True)
    visit = models.OneToOneField(
        "properties.PropertyVisit", on_delete=models.PROTECT, null=True, blank=True
    )
    interest = models.OneToOneField(
        "features.RentalInterest", on_delete=models.PROTECT, null=True, blank=True
    )


class HousingRequest(TimeStampedModel):
    academic_plan = models.ForeignKey(
        "features.AcademicHousingPlan",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="housing_requests",
    )
    academic_revision = models.PositiveIntegerField(null=True, blank=True)
    academic_snapshot = models.JSONField(default=dict)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="housing_requests",
    )
    title = models.CharField(max_length=160)
    note = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, default="published")
    visibility = models.CharField(max_length=30, default="eligible_owners")
    revision = models.PositiveIntegerField(default=1)
    criteria = models.JSONField(default=dict)
    expires_at = models.DateTimeField()


class HousingOffer(TimeStampedModel):
    student_policy_snapshot = models.JSONField(default=dict)
    request = models.ForeignKey(
        HousingRequest, on_delete=models.PROTECT, related_name="offers"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="housing_offers",
    )
    property = models.ForeignKey("properties.Property", on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    request_revision = models.PositiveIntegerField()
    status = models.CharField(max_length=20, default="sent")
    selection = models.JSONField(default=dict)
    note = models.TextField(blank=True, default="")
    rent_minor = models.PositiveBigIntegerField()
    deposit_minor = models.PositiveBigIntegerField(null=True, blank=True)
    price_period = models.CharField(max_length=20)
