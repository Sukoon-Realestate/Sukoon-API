"""Containers around canonical Property units; no alternative unit inventory."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from core_apps.common.models import TimeStampedModel


class ResidentialContainer(TimeStampedModel):
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=40)
    address = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    facilities = models.JSONField(default=list, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    elevators = models.PositiveSmallIntegerField(null=True, blank=True)
    parking_spaces = models.PositiveSmallIntegerField(null=True, blank=True)
    accessibility = models.TextField(blank=True)
    utilities = models.JSONField(default=dict, blank=True)
    included_services = models.JSONField(default=list, blank=True)
    public_access = models.TextField(blank=True)
    private_access = models.TextField(blank=True)
    contact_name = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=40, blank=True)
    unit_defaults = models.JSONField(default=dict, blank=True)
    revision = models.PositiveIntegerField(default=1)
    commercial_revision = models.PositiveIntegerField(default=1)
    topology_revision = models.PositiveIntegerField(default=1)
    authority_status = models.CharField(max_length=20, default="pending")
    authority_reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    authority_reference = models.CharField(max_length=200, blank=True)
    archived = models.BooleanField(default=False)

    class Meta:
        abstract = True


class ResidentialComplex(ResidentialContainer):
    declared_buildings = models.PositiveIntegerField(default=0)
    declared_standalone_units = models.PositiveIntegerField(default=0)


class ResidentialBuilding(ResidentialContainer):
    complex = models.ForeignKey(
        ResidentialComplex,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="buildings",
    )
    declared_units = models.PositiveIntegerField()
    floors = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["complex", "code"],
                condition=Q(complex__isnull=False),
                name="unique_building_code_in_complex",
            ),
            models.CheckConstraint(
                check=Q(declared_units__gte=1), name="building_declared_units_positive"
            ),
        ]


class PortfolioBatchItem(TimeStampedModel):
    """Successful items are durable independently of failures in the same batch."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    batch_key = models.UUIDField()
    item_key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    property = models.OneToOneField("Property", on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "batch_key", "item_key"],
                name="unique_portfolio_batch_item",
            )
        ]


class PortfolioBatch(TimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField(default=1)
    draft = models.JSONField(default=dict)
    results = models.JSONField(default=list)
    complete = models.BooleanField(default=False)


class PortfolioChangeSet(TimeStampedModel):
    """Immutable preview, then a durable per-unit result. Never an allocation."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    building = models.ForeignKey(
        ResidentialBuilding, on_delete=models.PROTECT, null=True
    )
    complex = models.ForeignKey(ResidentialComplex, on_delete=models.PROTECT, null=True)
    revision = models.PositiveIntegerField(default=1)
    operation = models.CharField(max_length=30)
    preview = models.JSONField(default=dict)
    results = models.JSONField(default=list)
    applied_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(building__isnull=False, complex__isnull=True)
                    | Q(building__isnull=True, complex__isnull=False)
                ),
                name="portfolio_change_exact_parent",
            )
        ]


class ResidentialMedia(TimeStampedModel):
    """Private immutable upload; public photos and authority evidence never mix."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    building = models.ForeignKey(
        ResidentialBuilding, on_delete=models.PROTECT, null=True, related_name="media"
    )
    complex = models.ForeignKey(
        ResidentialComplex, on_delete=models.PROTECT, null=True, related_name="media"
    )
    request_key = models.UUIDField()
    purpose = models.CharField(max_length=20)
    caption = models.CharField(max_length=300, blank=True)
    representative = models.BooleanField(default=False)
    sha256 = models.CharField(max_length=64)
    byte_size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=60)
    blob = models.CharField(max_length=500, blank=True)
    state = models.CharField(max_length=20, default="pending")
    review_status = models.CharField(max_length=20, default="pending")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )
    review_reason = models.TextField(blank=True)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "request_key"], name="unique_residential_media_request"
            ),
            models.CheckConstraint(
                check=(
                    Q(building__isnull=False, complex__isnull=True)
                    | Q(building__isnull=True, complex__isnull=False)
                ),
                name="residential_media_exact_parent",
            ),
        ]
