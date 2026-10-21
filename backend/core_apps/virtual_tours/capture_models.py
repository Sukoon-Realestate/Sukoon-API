"""Private camera inputs; these records never imply a publishable tour."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class PropertyCaptureSession(TimeStampedModel):
    property = models.ForeignKey(
        "properties.Property", on_delete=models.CASCADE, related_name="capture_sessions"
    )
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    client_id = models.UUIDField()
    state = models.CharField(max_length=24, default="draft")
    policy_version = models.CharField(max_length=48, default="rgb-tracking-v1")
    language = models.CharField(max_length=12, default="ar")
    revision = models.PositiveIntegerField(default=0)
    deleted_at = models.DateTimeField(null=True)
    coach_opt_in = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "client_id"], name="capture_owner_client_unique"
            )
        ]


class CaptureRoom(TimeStampedModel):
    session = models.ForeignKey(
        PropertyCaptureSession, on_delete=models.CASCADE, related_name="rooms"
    )
    client_id = models.UUIDField()
    label = models.CharField(max_length=80)
    confirmed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session", "client_id"], name="capture_room_client_unique"
            )
        ]


class CaptureAsset(TimeStampedModel):
    session = models.ForeignKey(
        PropertyCaptureSession, on_delete=models.CASCADE, related_name="assets"
    )
    client_id = models.UUIDField()
    sha256 = models.CharField(max_length=64)
    size = models.PositiveBigIntegerField()
    parts = models.JSONField(default=dict)
    blob = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=16, default="open")
    metadata = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session", "client_id"], name="capture_asset_client_unique"
            )
        ]


class CaptureManifestRevision(TimeStampedModel):
    session = models.ForeignKey(
        PropertyCaptureSession, on_delete=models.CASCADE, related_name="manifests"
    )
    revision = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    document = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session", "revision"], name="capture_manifest_revision_unique"
            ),
            models.UniqueConstraint(
                fields=["session", "sha256"], name="capture_manifest_hash_unique"
            ),
        ]


class CaptureProcessingJob(TimeStampedModel):
    manifest = models.ForeignKey(
        CaptureManifestRevision, on_delete=models.PROTECT, related_name="jobs"
    )
    profile = models.CharField(max_length=64, default="rgb-dual-v1")
    state = models.CharField(max_length=24, default="queued")
    stage = models.CharField(max_length=48, default="queued")
    outputs = models.JSONField(default=dict)
    attempt = models.PositiveIntegerField(default=0)
    lease_token = models.UUIDField(null=True)
    lease_until = models.DateTimeField(null=True)
    cancel_requested = models.BooleanField(default=False)
    diagnostics = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["manifest", "profile"], name="capture_logical_job_unique"
            )
        ]


class CaptureCoachSession(TimeStampedModel):
    session = models.ForeignKey(
        PropertyCaptureSession, on_delete=models.CASCADE, related_name="coach_sessions"
    )
    expires_at = models.DateTimeField()
    model = models.CharField(max_length=80)
    state = models.CharField(max_length=16, default="provisioning")
    # Credentials and media are intentionally never persisted.
