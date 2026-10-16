"""Private application snapshots and claims extending the existing review system."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from core_apps.common.models import TimeStampedModel


class ApplicationProfile(TimeStampedModel):
    applicant = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    desired_start = models.DateField(null=True, blank=True)
    months = models.PositiveSmallIntegerField(null=True, blank=True)
    occupants = models.PositiveSmallIntegerField(null=True, blank=True)
    introduction = models.TextField(blank=True, default="")


class ApplicationProfileVersion(TimeStampedModel):
    profile = models.ForeignKey(
        ApplicationProfile, on_delete=models.PROTECT, related_name="versions"
    )
    revision = models.PositiveIntegerField()
    snapshot = models.JSONField()
    digest = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "revision"],
                name="unique_application_profile_version",
            )
        ]


class ApplicationAccessGrant(TimeStampedModel):
    version = models.ForeignKey(
        ApplicationProfileVersion, on_delete=models.PROTECT, related_name="grants"
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="application_grants",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_application_grants",
    )
    property = models.ForeignKey("properties.Property", on_delete=models.PROTECT)
    purpose = models.CharField(max_length=50, default="rental_application")
    categories = models.JSONField(default=list)
    consent_digest = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    revision = models.PositiveIntegerField(default=1)


class RentalVerificationClaim(TimeStampedModel):
    """A scoped assertion, never a substitute for identity/property permissions."""

    subject_kind = models.CharField(
        max_length=30,
        choices=[
            ("identity", "Identity"),
            ("property_authority", "Property authority"),
            ("property_fact", "Property fact"),
            ("student_enrollment", "Student enrollment"),
        ],
    )
    subject_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_verification_claims",
    )
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="verification_claims",
    )
    kyc_submission = models.ForeignKey(
        "admin_api.KYCSubmission", on_delete=models.PROTECT, null=True, blank=True
    )
    claim_code = models.CharField(max_length=60)
    public_wording = models.CharField(max_length=240)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_rental_claims",
    )
    evidence_reference = models.CharField(max_length=160)
    student_evidence = models.ForeignKey(
        "RentalEvidence", on_delete=models.PROTECT, null=True, blank=True
    )
    campus = models.ForeignKey(
        "Campus", on_delete=models.PROTECT, null=True, blank=True
    )
    checked_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(
                        subject_kind="identity",
                        property__isnull=True,
                        kyc_submission__isnull=False,
                    )
                    | Q(
                        subject_kind__in=["property_authority", "property_fact"],
                        property__isnull=False,
                    )
                    | Q(
                        subject_kind="student_enrollment",
                        property__isnull=True,
                        student_evidence__isnull=False,
                        expires_at__isnull=False,
                    )
                ),
                name="rental_claim_exact_subject",
            )
        ]


class RentalConsentRecord(TimeStampedModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    subject_kind = models.CharField(max_length=40)
    subject_id = models.UUIDField()
    subject_revision = models.PositiveIntegerField()
    terms_digest = models.CharField(max_length=64)
    decision = models.CharField(max_length=30)
    policy_version = models.CharField(max_length=40)
    snapshot = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "actor",
                    "subject_kind",
                    "subject_id",
                    "subject_revision",
                    "decision",
                ],
                name="unique_rental_consent_decision",
            )
        ]
