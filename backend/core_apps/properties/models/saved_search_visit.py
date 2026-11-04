from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class SavedSearchVisit(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    workspace = models.CharField(max_length=16)
    identity_hash = models.CharField(max_length=64)
    identity = models.TextField()
    definition_hash = models.CharField(max_length=64)
    revision = models.PositiveIntegerField(default=1)
    last_read_at = models.DateTimeField(null=True, blank=True)
    versions = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "workspace", "identity_hash"],
                name="saved_search_visit_account_identity",
            )
        ]


class SavedSearchRead(TimeStampedModel):
    visit = models.ForeignKey(
        SavedSearchVisit, on_delete=models.CASCADE, related_name="reads"
    )
    definition_hash = models.CharField(max_length=64)
    base_revision = models.PositiveIntegerField()
    versions = models.JSONField(default=dict)
    changes = models.JSONField(default=dict)
    baseline_state = models.CharField(max_length=24)
    read_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    acknowledged_at = models.DateTimeField(null=True, blank=True)
