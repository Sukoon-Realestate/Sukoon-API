"""Physical item continuity, independent of bookable inventory and liability."""

from django.conf import settings
from django.db import models
from django.db.models import Q, F
from core_apps.common.models import TimeStampedModel


class AssetItem(TimeStampedModel):
    property = models.ForeignKey(
        "properties.Property", on_delete=models.PROTECT, related_name="asset_items"
    )
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT
    )
    label = models.CharField(max_length=200)
    category = models.CharField(max_length=80)
    make_model = models.CharField(max_length=160, blank=True)
    serial_number = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=30, default="active")
    revision = models.PositiveIntegerField(default=1)
    predecessor = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="successor",
    )


class AssetLocationPeriod(TimeStampedModel):
    asset = models.ForeignKey(
        AssetItem, on_delete=models.PROTECT, related_name="locations"
    )
    property = models.ForeignKey("properties.Property", on_delete=models.PROTECT)
    room_id = models.CharField(max_length=90, blank=True)
    space_label = models.CharField(max_length=120, blank=True)
    starts_on = models.DateField()
    ends_on_exclusive = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["asset"],
                condition=Q(ends_on_exclusive__isnull=True),
                name="asset_one_current_location",
            ),
            models.CheckConstraint(
                check=Q(ends_on_exclusive__isnull=True)
                | Q(ends_on_exclusive__gte=F("starts_on")),
                name="asset_location_valid_dates",
            ),
        ]


class AssetLifecycleEvent(TimeStampedModel):
    asset = models.ForeignKey(
        AssetItem, on_delete=models.PROTECT, related_name="events"
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=30)
    effective_on = models.DateField()
    from_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="asset_events_from",
    )
    to_property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="asset_events_to",
    )
    related_asset = models.ForeignKey(
        AssetItem,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="related_events",
    )


class AssetObservation(TimeStampedModel):
    asset = models.ForeignKey(
        AssetItem, on_delete=models.PROTECT, related_name="observations"
    )
    property = models.ForeignKey("properties.Property", on_delete=models.PROTECT)
    lease = models.ForeignKey("features.Lease", on_delete=models.PROTECT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    observed_on = models.DateField()
    condition = models.CharField(max_length=24, default="not_inspected")
    note = models.TextField(blank=True)
    capture_context = models.JSONField(default=dict)
    source_kind = models.CharField(max_length=24)
    source_id = models.UUIDField()
    source_revision = models.PositiveIntegerField()
    source_status = models.CharField(max_length=40)
    evidence = models.ManyToManyField(
        "features.RentalEvidence", blank=True, related_name="asset_observations"
    )


class AssetAnalysisJob(TimeStampedModel):
    asset = models.ForeignKey(
        AssetItem, on_delete=models.PROTECT, related_name="analysis_jobs"
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    previous_run = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True
    )
    revision = models.PositiveIntegerField(default=1)
    state = models.CharField(max_length=30, default="queued")
    source_manifest = models.JSONField()
    source_digest = models.CharField(max_length=64)
    provider = models.CharField(max_length=60, default="mock_asset_rules")
    provider_version = models.CharField(max_length=60, default="asset-review-v2")
    failure_code = models.CharField(max_length=60, blank=True)
    cancellation_requested = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)


class AssetAnalysisSuggestion(TimeStampedModel):
    job = models.ForeignKey(
        AssetAnalysisJob, on_delete=models.PROTECT, related_name="suggestions"
    )
    revision = models.PositiveIntegerField(default=1)
    kind = models.CharField(max_length=40)
    uncertainty = models.CharField(max_length=40)
    output = models.JSONField()
    review_status = models.CharField(max_length=32, default="ready_for_review")
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    review_note = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)


class AssetSharedSystem(TimeStampedModel):
    building = models.ForeignKey(
        "properties.ResidentialBuilding", on_delete=models.PROTECT
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    name = models.CharField(max_length=160)
    kind = models.CharField(max_length=40)
    authority_reference = models.CharField(max_length=200)
    assets = models.ManyToManyField(AssetItem, related_name="shared_systems")


class AssetPatternCase(TimeStampedModel):
    system = models.ForeignKey(
        AssetSharedSystem, on_delete=models.PROTECT, related_name="cases"
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    state = models.CharField(max_length=32, default="investigation_required")
    symptom = models.CharField(max_length=40)
    source_manifest = models.JSONField()
    source_digest = models.CharField(max_length=64)
    hypothesis = models.JSONField()
    resolution_source_kind = models.CharField(max_length=24, blank=True)
    resolution_source_id = models.UUIDField(null=True, blank=True)
    resolution_source_revision = models.PositiveIntegerField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)


class AssetWarrantyReference(TimeStampedModel):
    service_case = models.ForeignKey(
        "RentalOperationalCase", on_delete=models.PROTECT, null=True, blank=True
    )
    provider_result = models.JSONField(default=dict)
    asset = models.ForeignKey(
        AssetItem, on_delete=models.PROTECT, related_name="warranty_references"
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    issuer = models.CharField(max_length=160)
    reference = models.CharField(max_length=160)
    starts_on = models.DateField()
    ends_on_exclusive = models.DateField()
    source_kind = models.CharField(max_length=24)
    source_id = models.UUIDField()
    source_revision = models.PositiveIntegerField()
    status = models.CharField(max_length=24, default="recorded_unverified")
    claim_note = models.TextField(blank=True)
    mock_result = models.JSONField(default=dict)
