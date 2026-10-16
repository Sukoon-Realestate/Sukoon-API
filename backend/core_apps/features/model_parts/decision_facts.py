"""Selection-aware disclosed facts and explicit availability confirmations."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class PropertyDecisionFact(TimeStampedModel):
    property = models.ForeignKey(
        "properties.Property", on_delete=models.PROTECT, related_name="decision_facts"
    )
    offer_id = models.CharField(max_length=64, blank=True, default="")
    code = models.CharField(max_length=60)
    value = models.TextField(blank=True, default="")
    classification = models.CharField(
        max_length=20,
        choices=[
            ("owner_reported", "Owner reported"),
            ("verified", "Verified"),
            ("estimated", "Estimated"),
            ("unknown", "Unknown"),
        ],
        default="owner_reported",
    )
    claim = models.ForeignKey(
        "RentalVerificationClaim", on_delete=models.PROTECT, null=True, blank=True
    )
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    checked_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["property", "offer_id", "code"],
                name="unique_selection_decision_fact",
            )
        ]


class RentalAvailabilityConfirmation(TimeStampedModel):
    property = models.OneToOneField(
        "properties.Property",
        on_delete=models.PROTECT,
        related_name="rental_confirmation",
    )
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    inventory_revision = models.PositiveIntegerField()
    confirmed_at = models.DateTimeField()
    revision = models.PositiveIntegerField(default=1)
