from django.db import models
from django.utils import timezone

class PushDelivery(models.Model):
    notification = models.ForeignKey('notifications.Notification', on_delete=models.CASCADE)
    device = models.ForeignKey('notifications.DeviceToken', on_delete=models.CASCADE)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now, db_index=True)
    claimed_until = models.DateTimeField(null=True)
    accepted_at = models.DateTimeField(null=True)
    suppressed = models.BooleanField(default=False)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['notification', 'device'], name='unique_notification_device_delivery')]
