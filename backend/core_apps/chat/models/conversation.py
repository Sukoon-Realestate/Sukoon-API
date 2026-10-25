from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core_apps.common.models import TimeStampedModel


class Conversation(TimeStampedModel):
    consent_revision = models.PositiveIntegerField(default=0)
    # Compatibility only while the previous API process drains during rollout.
    # Inbox access and API responses no longer use this retired flag.
    workspace_archived = models.BooleanField(default=False)
    direct_context_key = models.CharField(max_length=128, null=True, blank=True, unique=True, editable=False)
    direct_pair_key = models.CharField(
        max_length=73, null=True, blank=True, unique=True, editable=False
    )
    kind = models.CharField(max_length=24, default="direct", db_index=True)
    housing_group = models.OneToOneField(
        "features.HousingGroup",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="chat_conversation",
    )
    company_request = models.OneToOneField(
        "features.CompanyHousingRequest",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="discussion",
    )
    last_sequence = models.PositiveBigIntegerField(default=0)
    last_event_sequence = models.PositiveBigIntegerField(default=0)
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
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(
                        kind="direct",
                        housing_group__isnull=True,
                        company_request__isnull=True,
                    )
                    | models.Q(
                        kind="housing_group",
                        housing_group__isnull=False,
                        company_request__isnull=True,
                    )
                    | models.Q(
                        kind="company_request",
                        housing_group__isnull=True,
                        company_request__isnull=False,
                    )
                ),
                name="chat_conversation_kind_group_consistent",
            )
        ]

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
    membership = models.ForeignKey(
        "features.GroupMembership",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    company_membership = models.ForeignKey(
        "features.CompanyMembership",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    membership_revision = models.PositiveBigIntegerField(default=0)
    membership_period = models.UUIDField(null=True, blank=True)
    visible_from_sequence = models.PositiveBigIntegerField(default=1)
    last_read_sequence = models.PositiveBigIntegerField(default=0)
    pinned_at = models.DateTimeField(null=True, blank=True)
    unread_reminder_sequence = models.PositiveBigIntegerField(null=True, blank=True)
    muted_until = models.DateTimeField(null=True, blank=True)
    is_muted = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    hidden_through_sequence = models.PositiveBigIntegerField(null=True, blank=True)

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
