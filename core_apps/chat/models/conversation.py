from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core_apps.common.models import TimeStampedModel


class Conversation(TimeStampedModel):
    # ? M2M through ConversationParticipant to store per-user unread_count and last_read_at
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="chat.ConversationParticipant",
        related_name="conversations",
    )
    # * Denormalized for O(1) conversation list rendering without subqueries
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_message_preview = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")
        ordering = ["-last_message_at"]

    def __str__(self) -> str:
        return f"Conversation {self.id}"


class ConversationParticipant(TimeStampedModel):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="participant_set",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation_participants",
        db_index=True,
    )
    last_read_at = models.DateTimeField(null=True, blank=True)
    # * Denormalized per-participant unread count — avoids N+1 on conversation list
    unread_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Conversation Participant")
        verbose_name_plural = _("Conversation Participants")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"],
                name="unique_participant_per_conversation",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.email} in {self.conversation.id}"
