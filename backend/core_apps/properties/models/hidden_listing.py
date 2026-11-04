from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class HiddenListingPreference(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    property = models.ForeignKey("properties.Property", on_delete=models.CASCADE)
    # Empty means the complete physical property, never an inferred offer.
    offer_id = models.CharField(max_length=64, blank=True, default="")
    expires_at = models.DateTimeField(null=True, blank=True)
    hidden = models.BooleanField(default=True)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "property", "offer_id"],
                name="hidden_listing_account_target",
            )
        ]
