from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class ChatEvent(TimeStampedModel):
    """Committed, ordered mutations; payload contains references, not media URLs."""

    conversation = models.ForeignKey("chat.Conversation", on_delete=models.CASCADE)
    sequence = models.PositiveBigIntegerField()
    kind = models.CharField(max_length=40)
    message = models.ForeignKey("chat.Message", null=True, on_delete=models.SET_NULL)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    data = models.JSONField(default=dict)
    delivered_at = models.DateTimeField(null=True)
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "sequence"],
                name="unique_chat_event_sequence",
            )
        ]


class ChatNotificationDelivery(TimeStampedModel):
    event = models.ForeignKey(ChatEvent, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notification = models.OneToOneField(
        "notifications.Notification",
        null=True,
        on_delete=models.SET_NULL,
    )
    push_claimed_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"],
                name="unique_chat_notification_delivery",
            )
        ]
