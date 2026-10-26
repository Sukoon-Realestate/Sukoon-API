"""Account erasure review preserves obligations and its decision history."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class AccountClosureRequest(TimeStampedModel):
    class Status(models.TextChoices):
        REVIEW = "in_review", "Under review"
        WAITING = "awaiting_settlement", "Awaiting settlement"
        WITHDRAWN = "withdrawn", "Withdrawn"
        REJECTED = "rejected", "Rejected"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.REVIEW
    )
    active = models.BooleanField(default=True)
    revision = models.PositiveIntegerField(default=1)
    reason = models.CharField(max_length=1000, blank=True)
    decision_reason = models.CharField(max_length=2000, blank=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(active=True),
                name="one_active_account_closure",
            )
        ]


class AccountClosureDecision(TimeStampedModel):
    request = models.ForeignKey(
        AccountClosureRequest, on_delete=models.PROTECT, related_name="decisions"
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    action = models.CharField(max_length=24)
    reason = models.CharField(max_length=2000, blank=True)
    blockers = models.JSONField(default=list)


class AccountClosureNotice(TimeStampedModel):
    decision = models.OneToOneField(AccountClosureDecision, on_delete=models.PROTECT)
    email_to = models.EmailField()
    email_sent_at = models.DateTimeField(null=True)
    attempts = models.PositiveIntegerField(default=0)


class AccountProfileErasureFile(TimeStampedModel):
    """Delete unreferenced profile media without replaying account closure."""

    request = models.ForeignKey(AccountClosureRequest, on_delete=models.PROTECT)
    public_id = models.CharField(max_length=300)
    storage_type = models.CharField(
        max_length=20,
        default="upload",
        choices=[("upload", "Public"), ("authenticated", "Private")],
    )
    deleted_at = models.DateTimeField(null=True)
    attempts = models.PositiveIntegerField(default=0)
