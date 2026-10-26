from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel
from .notification import Notification


class NotificationScopePreference(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    scope = models.CharField(max_length=16, choices=Notification.Scope.choices)
    revision = models.PositiveIntegerField(default=1)
    push_enabled = models.BooleanField(default=True)
    visit_notifications = models.BooleanField(default=True)
    new_properties_in_area = models.BooleanField(default=True)
    owner_messages = models.BooleanField(default=True)
    property_updates = models.BooleanField(default=False)
    security_alerts = models.BooleanField(default=True)
    promotions_and_updates = models.BooleanField(default=False)
    last_used_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "scope"], name="one_notification_scope_preference"
            )
        ]
