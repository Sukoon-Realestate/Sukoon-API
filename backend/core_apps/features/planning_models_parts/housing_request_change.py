"""Immutable, authorized history of published housing-request content."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class HousingRequestChange(TimeStampedModel):
    request = models.ForeignKey(
        "features.HousingRequest", on_delete=models.PROTECT, related_name="changes"
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    from_revision = models.PositiveIntegerField()
    to_revision = models.PositiveIntegerField()
    before = models.JSONField()
    after = models.JSONField()
    fields = models.JSONField(default=list)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["request", "to_revision"],
                name="housing_request_change_revision",
            )
        ]
