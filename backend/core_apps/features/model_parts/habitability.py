"""Restrictions annotate canonical inventory; they never release occupied days."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class HabitabilityRestriction(TimeStampedModel):
    case = models.ForeignKey(
        "RentalOperationalCase",
        on_delete=models.PROTECT,
        related_name="habitability_restrictions",
    )
    unit = models.ForeignKey(
        "RentalInventoryUnit",
        on_delete=models.PROTECT,
        related_name="habitability_restrictions",
    )
    policy = models.ForeignKey("PolicyDecision", on_delete=models.PROTECT)
    assessed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    restricted_at = models.DateTimeField()
    review_at = models.DateTimeField()
    cleared_at = models.DateTimeField(null=True, blank=True)
    cleared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="habitability_clearances",
    )
    clearance_policy = models.ForeignKey(
        "PolicyDecision",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="habitability_clearances",
    )
    inspection_evidence = models.ManyToManyField("RentalEvidence", blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["case", "unit"],
                condition=models.Q(cleared_at__isnull=True),
                name="unique_open_case_restriction",
            )
        ]
