"""Coordination records reference canonical obligations; they never replace them."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class AdvancedExecution(TimeStampedModel):
    source_kind = models.CharField(max_length=32)
    source_id = models.UUIDField()
    source_revision = models.PositiveIntegerField()
    source_digest = models.CharField(max_length=64)
    digest = models.CharField(max_length=64)
    mode = models.CharField(max_length=32)
    policy_version = models.CharField(max_length=64)
    provider_mode = models.CharField(max_length=16, default="mock")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    state = models.CharField(max_length=32, default="awaiting_consents")
    context = models.JSONField(default=dict)
    required_actor_ids = models.JSONField(default=list)
    actors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="advanced_executions"
    )
    case = models.ForeignKey(
        "features.RentalOperationalCase", on_delete=models.PROTECT, null=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source_kind", "source_id", "digest"],
                name="unique_advanced_execution_snapshot",
            )
        ]


class AdvancedExecutionLeg(TimeStampedModel):
    execution = models.ForeignKey(
        AdvancedExecution, on_delete=models.PROTECT, related_name="legs"
    )
    key = models.CharField(max_length=100)
    canonical_kind = models.CharField(max_length=32, default="individual")
    canonical_id = models.UUIDField(null=True)
    specification = models.JSONField(default=dict)
    actor_ids = models.JSONField(default=list)
    state = models.CharField(max_length=32, default="proposed")
    lease = models.OneToOneField(
        "features.Lease",
        on_delete=models.PROTECT,
        null=True,
        related_name="advanced_execution_leg",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["execution", "key"], name="unique_advanced_execution_leg"
            )
        ]


class AdvancedExecutionConsent(TimeStampedModel):
    execution = models.ForeignKey(
        AdvancedExecution, on_delete=models.PROTECT, related_name="consents"
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    digest = models.CharField(max_length=64)
    decision = models.CharField(max_length=24)
    execution_revision = models.PositiveIntegerField()


class AdvancedExecutionStep(TimeStampedModel):
    execution = models.ForeignKey(
        AdvancedExecution, on_delete=models.PROTECT, related_name="steps"
    )
    leg = models.ForeignKey(
        AdvancedExecutionLeg, on_delete=models.PROTECT, null=True, related_name="steps"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True
    )
    kind = models.CharField(max_length=64)
    state = models.CharField(max_length=32)
    canonical_kind = models.CharField(max_length=40, blank=True)
    canonical_id = models.UUIDField(null=True)
    metadata = models.JSONField(default=dict)
