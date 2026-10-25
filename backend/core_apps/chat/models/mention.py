from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class MessageMention(TimeStampedModel):
    """A send-time recipient and an exact, independently acknowledged mention."""

    message = models.ForeignKey("chat.Message", on_delete=models.CASCADE, related_name="mention_receipts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    membership_period = models.UUIDField()
    seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user", "membership_period"],
                name="unique_chat_mention_recipient",
            )
        ]
        indexes = [models.Index(fields=["user", "membership_period", "seen_at"], name="chat_mention_pending_idx")]
