from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class PropertyModerationDecision(TimeStampedModel):
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        related_name="moderation_decisions",
    )
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    source_revision = models.PositiveIntegerField()
    source_version = models.CharField(max_length=64)
    snapshot = models.JSONField()
    action = models.CharField(max_length=30)
    public_reason = models.TextField(blank=True)
    internal_note = models.TextField(blank=True)
