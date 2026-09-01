from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from core_apps.common.models import TimeStampedModel

User = get_user_model()


class PropertyVisit(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = ("pending", _("Pending"))
        CONFIRMED = ("confirmed", _("Confirmed"))
        CANCELED = ("canceled", _("Canceled"))
        REJECTED = ("rejected", _("Rejected"))

    property = models.ForeignKey(
        "Property",
        on_delete=models.CASCADE,
        related_name="visits",
        verbose_name=_("Property"),
    )
    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="visits",
        verbose_name=_("Tenant"),
    )
    visit_date = models.DateField(_("Visit Date"))
    visit_time = models.TimeField(_("Visit Time"))
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    note = models.TextField(_("Note"), blank=True, default="")

    class Meta:
        verbose_name = _("Property Visit")
        verbose_name_plural = _("Property Visits")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "property", "visit_date", "visit_time"],
                name="unique_tenant_property_visit_slot",
            )
        ]

    def __str__(self):
        return f"Visit for {self.property.title} by {self.tenant.email} on {self.visit_date} at {self.visit_time}"


class OwnerAvailabilitySlot(TimeStampedModel):
    property = models.ForeignKey(
        "Property",
        on_delete=models.CASCADE,
        related_name="availability_slots",
        verbose_name=_("Property"),
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="availability_slots",
        verbose_name=_("Owner"),
    )
    date = models.DateField(_("Date"))
    time = models.TimeField(_("Time"))
    is_enabled = models.BooleanField(_("Is Enabled"), default=True)

    class Meta:
        verbose_name = _("Owner Availability Slot")
        verbose_name_plural = _("Owner Availability Slots")
        ordering = ["date", "time"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "date", "time"],
                name="unique_property_availability_slot",
            )
        ]

    def __str__(self):
        return f"{self.property.title} on {self.date} at {self.time}"


class PropertyVisitReview(TimeStampedModel):
    visit = models.OneToOneField(
        PropertyVisit,
        on_delete=models.CASCADE,
        related_name="review",
        verbose_name=_("Visit"),
    )
    overall_rating = models.PositiveSmallIntegerField(
        _("Overall Rating"), validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    cleanliness_rating = models.PositiveSmallIntegerField(
        _("Cleanliness Rating"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    listing_accuracy_rating = models.PositiveSmallIntegerField(
        _("Listing Accuracy Rating"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    owner_interaction_rating = models.PositiveSmallIntegerField(
        _("Owner Interaction Rating"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(_("Comment"), blank=True, default="")

    class Meta:
        verbose_name = _("Property Visit Review")
        verbose_name_plural = _("Property Visit Reviews")
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(overall_rating__range=(1, 5)),
                name="visit_review_overall_between_1_and_5",
            ),
            models.CheckConstraint(
                check=models.Q(cleanliness_rating__range=(1, 5)),
                name="visit_review_cleanliness_between_1_and_5",
            ),
            models.CheckConstraint(
                check=models.Q(listing_accuracy_rating__range=(1, 5)),
                name="visit_review_accuracy_between_1_and_5",
            ),
            models.CheckConstraint(
                check=models.Q(owner_interaction_rating__range=(1, 5)),
                name="visit_review_owner_between_1_and_5",
            ),
        ]

    def __str__(self):
        return f"{self.overall_rating}/5 for visit {self.visit.id}"
