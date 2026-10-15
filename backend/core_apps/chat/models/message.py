from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core_apps.common.models import TimeStampedModel


class Message(TimeStampedModel):
    conversation = models.ForeignKey(
        "chat.Conversation",
        on_delete=models.CASCADE,
        related_name="messages",
        db_index=True,
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        db_index=True,
    )
    content = models.TextField()
    client_message_id = models.UUIDField(null=True, blank=True)
    kind = models.CharField(max_length=16, default="text")
    sequence = models.PositiveBigIntegerField(null=True, blank=True)
    payload_fingerprint = models.CharField(max_length=64, blank=True, default="")
    reply_to = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="deleted_chat_messages",
    )
    system_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "sequence"], name="unique_chat_sequence",
            ),
            models.UniqueConstraint(
                fields=["conversation", "sender", "client_message_id"],
                name="unique_chat_client_message_id",
            )
        ]

    def __str__(self) -> str:
        return (
            f"{self.sender.email} @ {self.created_at:%H:%M} in {self.conversation.id}"
        )
