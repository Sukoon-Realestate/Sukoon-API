"""Academic context over canonical groups, requests, evidence and rental records."""

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from core_apps.common.models import TimeStampedModel


class University(TimeStampedModel):
    name_en = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    source_url = models.URLField(blank=True, default="")
    checked_on = models.DateField(null=True, blank=True)


class Campus(TimeStampedModel):
    university = models.ForeignKey(
        University, on_delete=models.PROTECT, related_name="campuses"
    )
    name_en = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200)
    city = models.ForeignKey("properties.City", on_delete=models.PROTECT)
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    active = models.BooleanField(default=True)
    source_url = models.URLField(blank=True, default="")
    checked_on = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(latitude__isnull=True, longitude__isnull=True)
                    | Q(
                        latitude__isnull=False,
                        longitude__isnull=False,
                        latitude__gte=-90,
                        latitude__lte=90,
                        longitude__gte=-180,
                        longitude__lte=180,
                    )
                ),
                name="campus_valid_coordinates",
            )
        ]


class StudentProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="student_profile",
    )
    revision = models.PositiveIntegerField(default=1)
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT, null=True, blank=True)
    institution_name = models.CharField(max_length=200, blank=True, default="")
    academic_stage = models.CharField(max_length=100, blank=True, default="")
    enrollment_status = models.CharField(max_length=30, default="admission_pending")
    study_start = models.DateField(null=True, blank=True)
    study_end = models.DateField(null=True, blank=True)
    preferences = models.JSONField(default=dict)
    roommate_disclosures = models.JSONField(default=list)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(study_start__isnull=True)
                | Q(study_end__isnull=True)
                | Q(study_end__gt=F("study_start")),
                name="student_profile_valid_dates",
            )
        ]


class AcademicHousingPlan(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="academic_plans",
    )
    group = models.ForeignKey(
        "HousingGroup",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="academic_plans",
    )
    previous_plan = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True
    )
    current_lease = models.ForeignKey(
        "Lease", on_delete=models.PROTECT, null=True, blank=True
    )
    label = models.CharField(max_length=160)
    period_kind = models.CharField(max_length=30, default="semester")
    starts_on = models.DateField()
    ends_on_exclusive = models.DateField()
    revision = models.PositiveIntegerField(default=1)
    requirements_revision = models.PositiveIntegerField(default=1)
    roster_revision = models.PositiveIntegerField(default=0)
    access_group_revision = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default="planning")
    budget_basis = models.CharField(max_length=20, default="per_person")
    criteria = models.JSONField(default=dict)
    requirements = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(ends_on_exclusive__gt=F("starts_on")),
                name="academic_plan_valid_dates",
            ),
            models.CheckConstraint(
                check=Q(budget_basis__in=["per_person", "whole_group"]),
                name="academic_plan_budget_basis",
            ),
        ]


class AcademicPlanParticipant(TimeStampedModel):
    plan = models.ForeignKey(
        AcademicHousingPlan, on_delete=models.PROTECT, related_name="participants"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    membership = models.ForeignKey(
        "GroupMembership", on_delete=models.PROTECT, null=True, blank=True
    )
    membership_period = models.PositiveIntegerField(default=0)
    lease = models.ForeignKey("Lease", on_delete=models.PROTECT, null=True, blank=True)
    status = models.CharField(max_length=20, default="invited")
    requirements = models.JSONField(default=dict)
    owner_disclosures = models.JSONField(default=list)
    reviewed_revision = models.PositiveIntegerField(default=0)
    reviewed_digest = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "user"], name="unique_academic_plan_participant"
            )
        ]


class AcademicRequirementRevision(TimeStampedModel):
    plan = models.ForeignKey(
        AcademicHousingPlan, on_delete=models.PROTECT, related_name="versions"
    )
    revision = models.PositiveIntegerField()
    snapshot = models.JSONField()
    digest = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "revision"], name="unique_academic_plan_revision"
            )
        ]


class SharedLivingAgreement(TimeStampedModel):
    """Social arrangements only. No lease, allocation, liability or access side effects."""

    plan = models.ForeignKey(
        AcademicHousingPlan, on_delete=models.PROTECT, related_name="arrangements"
    )
    proposed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    kind = models.CharField(max_length=20, default="shared_living")
    revision = models.PositiveIntegerField(default=1)
    terms_revision = models.PositiveIntegerField(default=1)
    plan_revision = models.PositiveIntegerField()
    roster_revision = models.PositiveIntegerField()
    starts_on = models.DateField()
    ends_on_exclusive = models.DateField()
    rules = models.JSONField(default=dict)
    participant_ids = models.JSONField(default=list)
    digest = models.CharField(max_length=64)
    status = models.CharField(max_length=20, default="proposed")

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(ends_on_exclusive__gt=F("starts_on")),
                name="student_arrangement_valid_dates",
            )
        ]


class StudentOfferPolicy(TimeStampedModel):
    property = models.ForeignKey(
        "properties.Property", on_delete=models.PROTECT, related_name="student_policies"
    )
    offer_id = models.CharField(max_length=64)
    offer_revision = models.PositiveIntegerField()
    revision = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)
    eligibility = models.CharField(max_length=30, default="open")
    period_kinds = models.JSONField(default=list)
    starts_on = models.DateField()
    ends_on_exclusive = models.DateField()
    expires_at = models.DateTimeField()
    terms = models.JSONField(default=dict)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["property", "offer_id"],
                condition=Q(active=True),
                name="one_active_student_offer_policy",
            ),
            models.CheckConstraint(
                check=Q(ends_on_exclusive__gt=F("starts_on")),
                name="student_policy_valid_dates",
            ),
        ]
