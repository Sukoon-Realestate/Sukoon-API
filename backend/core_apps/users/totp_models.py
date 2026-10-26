"""Staff factors and independent recovery; no raw codes in audit records."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class StaffSecurityIdentity(TimeStampedModel):
    # Provisioned after independent identity verification, never by a profile API.
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    person_reference = models.CharField(max_length=128, db_index=True)
    evidence_reference = models.CharField(max_length=200)
    known_channel_reference = models.CharField(max_length=200)
    designated_owner_reviewer = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="verified_staff_identities",
    )
    verification_method = models.CharField(max_length=30, blank=True)
    verification_digest = models.CharField(max_length=64, blank=True)


class TotpFactor(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    secret_ciphertext = models.TextField(blank=True)
    revision = models.PositiveIntegerField(default=1)
    confirmed_at = models.DateTimeField(null=True)
    last_counter = models.BigIntegerField(default=-1)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True)


class TotpRecoveryRequest(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    identity = models.ForeignKey(StaffSecurityIdentity, on_delete=models.PROTECT)
    person_reference = models.CharField(max_length=128)
    owner_request = models.BooleanField(default=False)
    designated_reviewer_ids = models.JSONField(default=list)
    reason = models.CharField(max_length=1000)
    status = models.CharField(max_length=30, default="pending")
    active = models.BooleanField(default=True)
    revision = models.PositiveIntegerField(default=1)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="totp_recovery_decisions",
    )
    decision_reason = models.CharField(max_length=1000, blank=True)
    verification_method = models.CharField(max_length=30, blank=True)
    verification_reference = models.CharField(max_length=200, blank=True)
    verified_at = models.DateTimeField(null=True)
    approved_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(active=True),
                name="one_active_totp_recovery_per_user",
            )
        ]


class TotpEnrollment(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    session = models.ForeignKey("users.AuthSession", on_delete=models.PROTECT)
    recovery = models.ForeignKey(
        TotpRecoveryRequest, on_delete=models.PROTECT, null=True
    )
    recovery_revision = models.PositiveIntegerField(default=0)
    initial_identity = models.ForeignKey(
        StaffSecurityIdentity,
        on_delete=models.PROTECT,
        null=True,
    )
    security_epoch = models.PositiveIntegerField()
    factor_revision = models.PositiveIntegerField()
    secret_ciphertext = models.TextField()
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recovery", "recovery_revision"],
                name="one_binding_per_recovery_revision",
            )
        ]


class TotpRecoveryDecision(TimeStampedModel):
    recovery = models.ForeignKey(
        TotpRecoveryRequest, on_delete=models.PROTECT, related_name="decisions"
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    decision = models.CharField(max_length=30)
    reason = models.CharField(max_length=1000)
    verification_method = models.CharField(max_length=30, blank=True)
    verification_reference = models.CharField(max_length=200, blank=True)


class SecurityNotice(TimeStampedModel):
    """Durable delivery receipts; retry only delivery, never a security command."""

    event = models.OneToOneField("users.SecurityEvent", on_delete=models.PROTECT)
    email_to = models.EmailField()
    notification = models.OneToOneField(
        "notifications.Notification",
        on_delete=models.PROTECT,
        null=True,
    )
    email_sent_at = models.DateTimeField(null=True)
    attempts = models.PositiveIntegerField(default=0)
