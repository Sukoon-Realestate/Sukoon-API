from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class PromotionOption(models.Model):
    """Published promotion options; existing options remain free by default."""

    id = models.SlugField(primary_key=True, max_length=40)
    title_en = models.CharField(max_length=150)
    title_ar = models.CharField(max_length=150)
    duration_days = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(365)]
    )
    amount_minor = models.PositiveBigIntegerField(default=0)
    currency = models.CharField(max_length=3, default="EGP")
    exponent = models.PositiveSmallIntegerField(default=2)
    active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    revision = models.PositiveIntegerField(default=1, editable=False)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.CheckConstraint(check=models.Q(currency="EGP", exponent=2), name="promotion_supported_money"),
            models.CheckConstraint(
                check=models.Q(duration_days__gte=1, duration_days__lte=365),
                name="valid_promotion_duration",
            )
        ]

    def __str__(self):
        return self.title_en
