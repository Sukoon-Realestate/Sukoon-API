from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from core_apps.common.models import TimeStampedModel


class PropertyFavorite(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="property_favorites",
        verbose_name=_("User"),
    )
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name=_("Property"),
    )

    class Meta:
        verbose_name = _("Property Favorite")
        verbose_name_plural = _("Property Favorites")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "property"], name="unique_property_favorite"
            )
        ]

    def __str__(self):
        return f"{self.user.email} favorited {self.property.title}"


class SavedProperty(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_properties",
        verbose_name=_("User"),
    )
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="saves",
        verbose_name=_("Property"),
    )

    class Meta:
        verbose_name = _("Saved Property")
        verbose_name_plural = _("Saved Properties")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "property"], name="unique_saved_property"
            )
        ]

    def __str__(self):
        return f"{self.user.email} saved {self.property.title}"


class PropertyRating(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="property_ratings",
        verbose_name=_("User"),
    )
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="ratings",
        verbose_name=_("Property"),
    )
    rating = models.PositiveSmallIntegerField(
        _("Rating"), validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        verbose_name = _("Property Rating")
        verbose_name_plural = _("Property Ratings")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "property"], name="unique_property_rating"
            ),
            models.CheckConstraint(
                check=models.Q(rating__gte=1, rating__lte=5),
                name="property_rating_between_1_and_5",
            ),
        ]

    def __str__(self):
        return f"{self.rating}/5 for {self.property.title} by {self.user.email}"
