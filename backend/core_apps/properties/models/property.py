from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from core_apps.common.models import TimeStampedModel
from core_apps.users.services.new_business import NewAccountBusinessMixin
from cloudinary.models import CloudinaryField

User = get_user_model()


class Property(NewAccountBusinessMixin, TimeStampedModel):
    account_party_paths = ('owner_id',)

    media_revision = models.PositiveIntegerField(default=0)
    review_revision = models.PositiveIntegerField(default=1, editable=False)
    moderation_blocked = models.BooleanField(default=False, editable=False)
    moderation_reason = models.TextField(blank=True, default="", editable=False)
    search_document = models.TextField(blank=True, default="", editable=False)
    # A direct complex parent is only for standalone units. Building membership
    # derives its complex through the building, so contradictory parents cannot exist.
    building = models.ForeignKey(
        "ResidentialBuilding",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="units",
    )
    complex = models.ForeignKey(
        "ResidentialComplex",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="standalone_units",
    )
    unit_code = models.CharField(max_length=40, blank=True, default="")
    occupancy_capacity = models.PositiveSmallIntegerField(null=True, blank=True)
    portfolio_inheritance = models.JSONField(default=dict, blank=True)
    retired_at = models.DateTimeField(null=True, blank=True)
    replaces = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="successors"
    )

    class PricePeriod(models.TextChoices):
        DAILY = ("daily", _("Daily"))
        WEEKLY = ("weekly", _("Weekly"))
        MONTHLY = ("monthly", _("Monthly"))
        YEARLY = ("yearly", _("Yearly"))

    class SuitableFor(models.TextChoices):
        FAMILIES = ("families", _("Families"))
        SINGLES = ("singles", _("Singles"))
        STUDENTS = ("students", _("Students"))
        FEMALE_STUDENTS = ("female_students", _("Female Students Only"))
        ALL = ("all", _("All"))

    class Status(models.TextChoices):
        VERIFIED = ("verified", _("Verified"))
        UNDER_REVIEW = ("under_review", _("Under Review"))
        NEEDS_REVISION = ("needs_revision", _("Needs Revision"))
        HIDDEN = ("hidden", _("Hidden"))

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="properties",
        verbose_name=_("Owner"),
    )
    main_image = CloudinaryField(
        folder="properties/main_images/",
        null=True,
        blank=True,
        verbose_name=_("Main Image"),
    )
    video = CloudinaryField(
        folder="properties/videos/",
        resource_type="video",
        null=True,
        blank=True,
        verbose_name=_("Property Video"),
    )
    video_duration = models.PositiveIntegerField(
        _("Video Duration (seconds)"), null=True, blank=True
    )
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True, default="")
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2, default=0)
    price_period = models.CharField(
        _("Price Period"),
        max_length=20,
        choices=PricePeriod.choices,
        default=PricePeriod.MONTHLY,
    )
    property_type = models.ForeignKey(
        "properties.PropertyType",
        on_delete=models.PROTECT,
        related_name="properties",
        verbose_name=_("Property Type"),
    )
    is_furnished = models.BooleanField(_("Is Furnished"), default=False)
    is_verified = models.BooleanField(_("Is Verified"), default=False)
    # ? Moderation state — only editable by admin/staff, never via the API
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.UNDER_REVIEW,
    )
    bedrooms = models.IntegerField(_("Bedrooms"), default=1)
    bathrooms = models.IntegerField(_("Bathrooms"), default=1)
    area = models.IntegerField(_("Area (sqm)"), default=0)
    space = models.CharField(_("Space"), max_length=50, blank=True, default="")
    floor = models.IntegerField(_("Floor"), null=True, blank=True)
    rental_period = models.IntegerField(_("Rental Period (months)"), default=1)
    suitable_for = models.CharField(
        _("Suitable For"),
        max_length=50,
        choices=SuitableFor.choices,
        default=SuitableFor.ALL,
    )
    smoking_allowed = models.BooleanField(
        _("Smoking Allowed"), null=True, blank=True, default=False
    )

    # Location
    governorate = models.ForeignKey(
        "properties.Governorate",
        on_delete=models.PROTECT,
        related_name="properties",
        verbose_name=_("Governorate"),
    )
    city = models.ForeignKey(
        "properties.City",
        on_delete=models.PROTECT,
        related_name="properties",
        verbose_name=_("City"),
    )
    district_catalog = models.ForeignKey(
        "District",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="properties",
    )
    district = models.CharField(_("District"), max_length=100)
    street = models.CharField(_("Street"), max_length=255, blank=True, default="")
    country = models.CharField(
        _("Country"), max_length=100, blank=True, default="Egypt"
    )
    building_year = models.PositiveIntegerField(
        _("Building Year"), null=True, blank=True
    )
    deposit = models.CharField(_("Deposit"), max_length=50, blank=True, default="")
    ownership_proof = CloudinaryField(
        folder="properties/ownership_proofs/",
        null=True,
        blank=True,
        verbose_name=_("Ownership Proof"),
    )
    is_ownership_verified = models.BooleanField(
        _("Is Ownership Verified"), default=False
    )
    latitude = models.DecimalField(
        _("Latitude"), max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        _("Longitude"), max_digits=9, decimal_places=6, null=True, blank=True
    )
    availability_confirmed_at = models.DateTimeField(null=True, blank=True)
    rental_inventory = models.JSONField(default=dict, blank=True)
    rental_scopes = models.CharField(max_length=100, blank=True, default="")
    rental_min_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    rental_price_period = models.CharField(max_length=20, blank=True, default="")

    # Amenities
    has_wifi = models.BooleanField(_("Has Wi-Fi"), default=False)
    has_elevator = models.BooleanField(_("Has Elevator"), default=False)
    has_garage = models.BooleanField(_("Has Garage"), default=False)
    has_security = models.BooleanField(_("Has Security"), default=False)
    has_balcony = models.BooleanField(_("Has Balcony"), default=False)
    has_air_conditioning = models.BooleanField(_("Has Air Conditioning"), default=False)
    near_metro = models.BooleanField(_("Near Metro"), default=False)
    has_natural_gas = models.BooleanField(_("Has Natural Gas"), default=False)
    has_electricity_meter = models.BooleanField(
        _("Has Electricity Meter"), default=False
    )
    has_water_meter = models.BooleanField(_("Has Water Meter"), default=False)

    def clean(self):
        super().clean()
        if self.retired_at and self.status != self.Status.HIDDEN:
            from django.core.exceptions import ValidationError

            raise ValidationError({"status": "Retired inventory must remain hidden."})

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(retired_at__isnull=True) | models.Q(status="hidden"),
                name="retired_unit_remains_hidden",
            ),
            models.CheckConstraint(
                check=models.Q(building__isnull=True) | models.Q(complex__isnull=True),
                name="unit_has_one_direct_parent",
            ),
            models.CheckConstraint(
                check=models.Q(occupancy_capacity__isnull=True)
                | models.Q(occupancy_capacity__gte=1),
                name="unit_capacity_positive_or_unknown",
            ),
            models.UniqueConstraint(
                fields=["building", "unit_code"],
                condition=models.Q(building__isnull=False, retired_at__isnull=True)
                & ~models.Q(unit_code=""),
                name="unique_unit_code_in_building",
            ),
            models.UniqueConstraint(
                fields=["complex", "unit_code"],
                condition=models.Q(complex__isnull=False, retired_at__isnull=True)
                & ~models.Q(unit_code=""),
                name="unique_standalone_code_in_complex",
            ),
        ]
        verbose_name = _("Property")
        verbose_name_plural = _("Properties")
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["governorate", "city", "district"],
                name="property_location_idx",
            ),
            models.Index(fields=["price"], name="property_price_idx"),
            models.Index(fields=["-created_at"], name="property_created_at_idx"),
            models.Index(
                fields=["property_type", "price"], name="property_type_price_idx"
            ),
        ]

    def __str__(self):
        return self.title


class PropertyRequest(Property):
    """Admin moderation view of existing property submissions."""

    class Meta:
        proxy = True
        verbose_name = _("Property request")
        verbose_name_plural = _("Property requests")
        default_permissions = ()


class PropertyImage(TimeStampedModel):
    position = models.PositiveIntegerField(default=0)
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Property"),
    )
    image = CloudinaryField(
        folder="properties/images/",
        verbose_name=_("Property Image"),
    )
    name = models.CharField(_("Name"), max_length=255, blank=True, default="")
    description = models.TextField(_("Description"), blank=True, default="")

    class Meta:
        verbose_name = _("Property Image")
        verbose_name_plural = _("Property Images")

    def save(self, *args, **kwargs):
        from django.db import transaction
        with transaction.atomic():
            Property.objects.select_for_update().get(pk=self.property_id)
            return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.db import transaction
        with transaction.atomic():
            Property.objects.select_for_update().get(pk=self.property_id)
            return super().delete(*args, **kwargs)

    def __str__(self):
        return f"Image for property: {self.property.title}"
