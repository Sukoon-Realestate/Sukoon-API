from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class NotificationDeliveryPolicy(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    revision = models.PositiveIntegerField(default=1)
    timezone_name = models.CharField(max_length=64, default="Africa/Cairo")
    modes = models.JSONField(default=dict)
    quiet_start = models.PositiveSmallIntegerField(null=True)
    quiet_end = models.PositiveSmallIntegerField(null=True)


class NotificationDigestHold(TimeStampedModel):
    notification = models.OneToOneField("notifications.Notification", on_delete=models.CASCADE)
    policy_revision = models.PositiveIntegerField()
    due_at = models.DateTimeField(db_index=True)
    civil_day = models.DateField()
    state = models.CharField(max_length=16, default="pending")
    summary = models.ForeignKey("notifications.Notification", null=True, on_delete=models.SET_NULL, related_name="digest_sources")


class NotificationDailyDigest(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    civil_day = models.DateField()
    notification = models.OneToOneField("notifications.Notification", on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "civil_day"], name="unique_account_digest_civil_day")]
