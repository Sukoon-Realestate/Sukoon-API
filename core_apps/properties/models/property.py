from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from core_apps.common.models import TimeStampedModel
from cloudinary.models import CloudinaryField

User = get_user_model()


class Property(TimeStampedModel):
    class PricePeriod(models.TextChoices):
        DAILY = ("daily", _("Daily"))
        WEEKLY = ("weekly", _("Weekly"))
        MONTHLY = ("monthly", _("Monthly"))
        YEARLY = ("yearly", _("Yearly"))

    class PropertyType(models.TextChoices):
        APARTMENT = ("apartment", _("Apartment"))
        HOUSE = ("house", _("House"))
        VILLA = ("villa", _("Villa"))
        STUDIO = ("studio", _("Studio"))
        PENTHOUSE = ("penthouse", _("Penthouse"))

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
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True, default="")
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2)
    price_period = models.CharField(
        _("Price Period"),
        max_length=20,
        choices=PricePeriod.choices,
        default=PricePeriod.MONTHLY,
    )
    property_type = models.CharField(
        _("Property Type"),
        max_length=20,
        choices=PropertyType.choices,
        default=PropertyType.APARTMENT,
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
    smoking_allowed = models.BooleanField(_("Smoking Allowed"), default=False)

    # Location
    country = models.CharField(_("Country"), max_length=100, default="Egypt")
    city = models.CharField(_("City"), max_length=100)
    district = models.CharField(_("District"), max_length=100)
    latitude = models.DecimalField(
        _("Latitude"), max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        _("Longitude"), max_digits=9, decimal_places=6, null=True, blank=True
    )

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

    class Meta:
        verbose_name = _("Property")
        verbose_name_plural = _("Properties")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["city", "district"], name="property_location_idx"),
            models.Index(fields=["price"], name="property_price_idx"),
            models.Index(fields=["-created_at"], name="property_created_at_idx"),
            models.Index(
                fields=["property_type", "price"], name="property_type_price_idx"
            ),
        ]

    def __str__(self):
        return self.title


class PropertyImage(TimeStampedModel):
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

    def __str__(self):
        return f"Image for property: {self.property.title}"
