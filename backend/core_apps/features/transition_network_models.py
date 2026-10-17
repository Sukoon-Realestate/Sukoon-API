"""Assisted move planning; canonical leases remain the source of obligations."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from core_apps.common.models import TimeStampedModel


class MoveIntent(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    lease = models.ForeignKey("features.Lease", on_delete=models.PROTECT)
    source_transition = models.ForeignKey(
        "features.TenancyTransition", on_delete=models.PROTECT
    )
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, default="draft")
    criteria = models.JSONField(default=dict)
    max_deposit_minor = models.PositiveBigIntegerField()
    max_gap_days = models.PositiveSmallIntegerField(default=0)
    turnover_days = models.PositiveSmallIntegerField(default=1)
    matching_consent = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["lease", "user"],
                condition=~Q(status__in=["withdrawn", "expired"]),
                name="one_live_move_intent",
            ),
            models.CheckConstraint(
                check=Q(turnover_days__gte=1), name="move_turnover_positive"
            ),
        ]


class TransitionMatchRun(TimeStampedModel):
    intent = models.ForeignKey(
        MoveIntent, on_delete=models.PROTECT, related_name="runs"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    input_revision = models.PositiveIntegerField()
    status = models.CharField(max_length=24, default="queued")
    result_status = models.CharField(max_length=24, default="unknown")
    searched_count = models.PositiveIntegerField(default=0)
    pool_limited = models.BooleanField(default=False)
    failure_code = models.CharField(max_length=80, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class TransitionCandidate(TimeStampedModel):
    run = models.ForeignKey(
        TransitionMatchRun, on_delete=models.PROTECT, related_name="candidates"
    )
    revision = models.PositiveIntegerField(default=1)
    snapshot = models.JSONField(default=dict)
    snapshot_digest = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=24, default="collecting_interest")


class TransitionParticipant(TimeStampedModel):
    candidate = models.ForeignKey(
        TransitionCandidate, on_delete=models.PROTECT, related_name="participants"
    )
    intent = models.ForeignKey(MoveIntent, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    intent_revision = models.PositiveIntegerField()
    decision = models.CharField(max_length=20, default="pending")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "user"], name="unique_transition_participant"
            )
        ]
