"""Authoring documents are versioned as a unit; delivery variants are immutable."""

from django.conf import settings
from builtins import property as computed_property
from django.db import models
from core_apps.common.models import TimeStampedModel


class PropertyVirtualTour(TimeStampedModel):
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="virtual_tours",
        null=True,
        blank=True,
    )
    building = models.ForeignKey(
        "properties.ResidentialBuilding",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="virtual_tours",
    )
    complex = models.ForeignKey(
        "properties.ResidentialComplex",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="virtual_tours",
    )

    @computed_property
    def target(self):
        return self.property or self.building or self.complex

    @computed_property
    def target_kind(self):
        return (
            "property"
            if self.property_id
            else "building" if self.building_id else "complex"
        )

    kind = models.CharField(
        max_length=24, choices=[("panorama_360", "360°"), ("model_3d", "3D")]
    )
    active_revision = models.ForeignKey(
        "TourRevision",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    disabled = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["property", "kind"], name="unique_property_tour_kind"
            ),
            models.UniqueConstraint(
                fields=["building", "kind"], name="unique_building_tour_kind"
            ),
            models.UniqueConstraint(
                fields=["complex", "kind"], name="unique_complex_tour_kind"
            ),
            models.CheckConstraint(
                check=(
                    models.Q(
                        property__isnull=False,
                        building__isnull=True,
                        complex__isnull=True,
                    )
                    | models.Q(
                        property__isnull=True,
                        building__isnull=False,
                        complex__isnull=True,
                    )
                    | models.Q(
                        property__isnull=True,
                        building__isnull=True,
                        complex__isnull=False,
                    )
                ),
                name="tour_exact_asset_target",
            ),
        ]


class TourRevision(TimeStampedModel):
    tour = models.ForeignKey(
        PropertyVirtualTour, on_delete=models.CASCADE, related_name="revisions"
    )
    capture_job = models.ForeignKey(
        "CaptureProcessingJob", null=True, blank=True,
        on_delete=models.PROTECT, related_name="tour_revisions",
    )
    draft_version = models.PositiveIntegerField(default=1)
    authoring = models.JSONField(default=dict)
    source_hash = models.CharField(max_length=64, blank=True)
    processing_state = models.CharField(max_length=20, default="draft")
    processing_token = models.UUIDField(null=True, editable=False)
    review_state = models.CharField(max_length=20, default="not_submitted")
    stage = models.CharField(max_length=40, blank=True)
    report = models.JSONField(default=dict)
    processor_version = models.CharField(max_length=40, blank=True)
    submitted_at = models.DateTimeField(null=True)


class TourAsset(TimeStampedModel):
    revision = models.ForeignKey(
        TourRevision, on_delete=models.CASCADE, related_name="assets"
    )
    role = models.CharField(max_length=24)
    # An opaque immutable blob shared by clones. Never returned by public APIs.
    blob = models.CharField(max_length=80)
    sha256 = models.CharField(max_length=64)
    size = models.PositiveBigIntegerField()
    media_type = models.CharField(max_length=80)


class TourVariant(TimeStampedModel):
    revision = models.ForeignKey(
        TourRevision, on_delete=models.CASCADE, related_name="variants"
    )
    context = models.CharField(max_length=80)  # overview or persisted offer UUID
    scope_fingerprint = models.CharField(max_length=64)
    source_hash = models.CharField(max_length=64)
    manifest = models.JSONField()
    # resource ID -> immutable blob or tile-set directory; private server-side only.
    resources = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["revision", "context"], name="unique_tour_variant_context"
            )
        ]


class TourUploadSession(TimeStampedModel):
    revision = models.ForeignKey(
        TourRevision, on_delete=models.CASCADE, related_name="uploads"
    )
    role = models.CharField(max_length=24)
    size = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    media_type = models.CharField(max_length=80)
    state = models.CharField(max_length=20, default="open")
    parts = models.JSONField(default=dict)
    asset = models.ForeignKey(TourAsset, null=True, on_delete=models.SET_NULL)
    expires_at = models.DateTimeField()


class TourOperation(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    key = models.CharField(max_length=100)
    action = models.CharField(max_length=60)
    resource = models.CharField(max_length=100)
    request_hash = models.CharField(max_length=64)
    status = models.CharField(max_length=20, default="pending")
    result = models.JSONField(default=dict)
    http_status = models.PositiveSmallIntegerField(default=200)
    expires_at = models.DateTimeField()

    # Retain key/hash tombstones after receipts expire; never replay as a new write.
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "key"], name="unique_tour_operation_key"
            )
        ]


class TourViewerSession(TimeStampedModel):
    variant = models.ForeignKey(TourVariant, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE
    )
    preview = models.BooleanField(default=False)
    bootstrap_hash = models.CharField(max_length=64, unique=True)
    bootstrap_expires_at = models.DateTimeField()
    exchanged_at = models.DateTimeField(null=True)
    credential_hash = models.CharField(max_length=64, blank=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True)


class TourReviewEvent(TimeStampedModel):
    revision = models.ForeignKey(
        TourRevision, on_delete=models.CASCADE, related_name="reviews"
    )
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    decision = models.CharField(max_length=20)
    source_hash = models.CharField(max_length=64)
    reason = models.TextField(blank=True)


from .capture_models import (  # noqa: E402,F401
    PropertyCaptureSession, CaptureRoom, CaptureAsset, CaptureManifestRevision,
    CaptureProcessingJob, CaptureCoachSession,
)
