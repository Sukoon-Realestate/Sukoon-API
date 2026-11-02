from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class OwnerRentalAchievement(TimeStampedModel):
    tenancy_root_id = models.UUIDField(unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    lease = models.ForeignKey("features.Lease", on_delete=models.PROTECT)
    revoked = models.BooleanField(default=False)


class OwnerMilestone(TimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tier = models.CharField(max_length=12)
    threshold = models.PositiveIntegerField()
    acknowledged_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "tier"], name="owner_milestone_once"
            )
        ]
