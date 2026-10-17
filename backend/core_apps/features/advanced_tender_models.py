"""Additive coordination records; inventory, demand and tenancy stay canonical."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class HousingTender(TimeStampedModel):
    group = models.ForeignKey(
        "features.HousingGroup", on_delete=models.PROTECT, related_name="tenders"
    )
    request = models.ForeignKey(
        "features.HousingRequest", on_delete=models.PROTECT, related_name="tenders"
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    title = models.CharField(max_length=160)
    member_access = models.JSONField(default=dict)
    source_context = models.JSONField(default=dict)
    revision = models.PositiveIntegerField(default=1)
    roster_revision = models.PositiveIntegerField()
    request_revision = models.PositiveIntegerField()
    status = models.CharField(max_length=32, default="collecting_requirements")
    closes_at = models.DateTimeField()
    active_snapshot = models.ForeignKey(
        "features.TenderDemandSnapshot",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )


class TenderParticipantRequirement(TimeStampedModel):
    tender = models.ForeignKey(
        HousingTender, on_delete=models.PROTECT, related_name="requirements"
    )
    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    roster_revision = models.PositiveIntegerField()
    request_revision = models.PositiveIntegerField()
    values = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tender", "participant", "revision"],
                name="unique_tender_person_revision",
            )
        ]


class TenderDemandSnapshot(TimeStampedModel):
    tender = models.ForeignKey(
        HousingTender, on_delete=models.PROTECT, related_name="snapshots"
    )
    revision = models.PositiveIntegerField()
    roster_revision = models.PositiveIntegerField()
    request_revision = models.PositiveIntegerField()
    digest = models.CharField(max_length=64)
    private_requirements = models.JSONField(default=list)
    owner_projection = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tender", "revision"], name="unique_tender_snapshot_revision"
            )
        ]


class OwnerBid(TimeStampedModel):
    tender = models.ForeignKey(
        HousingTender, on_delete=models.PROTECT, related_name="bids"
    )
    snapshot = models.ForeignKey(TenderDemandSnapshot, on_delete=models.PROTECT)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=24, default="submitted")
    expires_at = models.DateTimeField()
    start_on = models.DateField()
    end_on = models.DateField()
    minimum_quantity = models.PositiveSmallIntegerField(default=1)
    combines = models.BooleanField(default=True)
    pricing_rule = models.CharField(max_length=20, default="canonical")
    price_tiers = models.JSONField(default=list)
    supersedes = models.OneToOneField(
        "self", on_delete=models.PROTECT, null=True, related_name="replacement"
    )


class TenderBidLine(TimeStampedModel):
    bid = models.ForeignKey(OwnerBid, on_delete=models.PROTECT, related_name="lines")
    offer = models.OneToOneField(
        "features.HousingOffer", on_delete=models.PROTECT, related_name="tender_line"
    )
    physical_keys = models.JSONField(default=list)


class PackageCandidate(TimeStampedModel):
    tender = models.ForeignKey(
        HousingTender, on_delete=models.PROTECT, related_name="packages"
    )
    snapshot = models.ForeignKey(TenderDemandSnapshot, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    digest = models.CharField(max_length=64)
    status = models.CharField(max_length=24, default="reviewing")
    execution_mode = models.CharField(max_length=32, default="independent_participants")
    allocations = models.JSONField(default=list)
    unallocated_ids = models.JSONField(default=list)
    total_rent_minor = models.PositiveBigIntegerField(default=0)
    total_deposit_minor = models.PositiveBigIntegerField(default=0)


class PackageConsent(TimeStampedModel):
    package = models.ForeignKey(
        PackageCandidate, on_delete=models.PROTECT, related_name="consents"
    )
    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    package_digest = models.CharField(max_length=64)
    decision = models.CharField(max_length=16)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["package", "participant"],
                name="unique_tender_package_person_consent",
            )
        ]


class TenderPackageRun(TimeStampedModel):
    tender = models.ForeignKey(
        HousingTender, on_delete=models.PROTECT, related_name="package_runs"
    )
    snapshot = models.ForeignKey(TenderDemandSnapshot, on_delete=models.PROTECT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=32, default="queued")
    source_digest = models.CharField(max_length=64)
    input = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    packages = models.ManyToManyField(
        PackageCandidate, related_name="construction_runs"
    )
    completed_at = models.DateTimeField(null=True)


class TenderBidClarification(TimeStampedModel):
    bid = models.ForeignKey(
        OwnerBid, on_delete=models.PROTECT, related_name="clarifications"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    bid_revision = models.PositiveIntegerField()
    text = models.CharField(max_length=1600)

    @property
    def revision(self):
        return 1  # Immutable append-only note; it cannot amend bid terms.
