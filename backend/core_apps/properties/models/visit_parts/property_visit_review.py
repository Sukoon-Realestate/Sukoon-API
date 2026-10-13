"""Visit: property visit review."""

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from core_apps.common.models import TimeStampedModel
from .property_visit import PropertyVisit


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
