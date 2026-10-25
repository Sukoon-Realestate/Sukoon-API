from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class MessageReaction(TimeStampedModel):
    message = models.ForeignKey(
        "chat.Message", on_delete=models.CASCADE, related_name="reactions"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    membership_period = models.UUIDField()
    emoji = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user"], name="unique_message_reaction_user"
            )
        ]
