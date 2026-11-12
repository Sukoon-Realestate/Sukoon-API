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
    acknowledged_read = models.ForeignKey(
        "SavedSearchRead", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "workspace", "identity_hash"],
                name="saved_search_visit_account_identity",
            )
        ]


class SavedSearchRead(TimeStampedModel):
    visit = models.ForeignKey(SavedSearchVisit, on_delete=models.CASCADE, related_name="reads")
    definition_hash = models.CharField(max_length=64)
    base_revision = models.PositiveIntegerField()
    versions = models.JSONField(default=dict)
    changes = models.JSONField(default=dict)
    baseline_state = models.CharField(max_length=24)
    read_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    # Nullable defaults allow older workers to insert legacy receipts during rollout.
    itemized = models.BooleanField(default=False, null=True)
    items_ready = models.BooleanField(default=True, null=True)

    class Meta:
        ordering = ["-created_at", "-updated_at"]
        indexes = [models.Index(fields=["expires_at", "pkid"], name="saved_read_expiry_idx")]


class SavedSearchReadItem(models.Model):
    pkid = models.BigAutoField(primary_key=True)
    read = models.ForeignKey(SavedSearchRead, on_delete=models.CASCADE, related_name="items", db_index=False)
    property_identity = models.UUIDField()
    review_revision = models.PositiveIntegerField()
    modified_at = models.DateTimeField()
    change = models.CharField(max_length=8, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["read", "property_identity"], name="unique_saved_read_property"),
            models.CheckConstraint(
                check=models.Q(change__in=["", "new", "updated"]), name="saved_read_item_change_valid"
            ),
        ]
