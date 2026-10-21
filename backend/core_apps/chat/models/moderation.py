"""Durable, private rental-chat review. Model output never grants authority."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class RentalChatContext(TimeStampedModel):
    conversation = models.OneToOneField(
        "chat.Conversation", on_delete=models.CASCADE, related_name="rental_context"
    )
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    properties = models.ManyToManyField("properties.Property", blank=True)
    source = models.CharField(max_length=24, default="rental_inquiry")


class ChatPolicyConsent(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    version = models.CharField(max_length=40)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "version"], name="chat_policy_consent_once"
            )
        ]


class ChatModerationInput(TimeStampedModel):
    message = models.ForeignKey("chat.Message", on_delete=models.CASCADE)
    revision = models.PositiveIntegerField()
    conversation = models.ForeignKey("chat.Conversation", on_delete=models.CASCADE)
    ciphertext = models.TextField()
    due_at = models.DateTimeField(db_index=True)
    state = models.CharField(max_length=20, default="pending", db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["message", "revision"], name="chat_review_message_revision"
            )
        ]


class ChatModerationBatch(TimeStampedModel):
    conversation = models.ForeignKey("chat.Conversation", on_delete=models.CASCADE)
    fingerprint = models.CharField(max_length=64, unique=True)
    input_ids = models.JSONField(default=list)
    state = models.CharField(max_length=24, default="pending", db_index=True)
    lease_token = models.UUIDField(null=True)
    lease_until = models.DateTimeField(null=True, db_index=True)
    next_attempt_at = models.DateTimeField(null=True)
    attempts = models.PositiveIntegerField(default=0)
    model = models.CharField(max_length=80, blank=True)
    policy_version = models.CharField(max_length=40)
    diagnostics = models.JSONField(default=dict)


class ChatMediaAnalysis(TimeStampedModel):
    attachment = models.ForeignKey("chat.ChatAttachment", on_delete=models.CASCADE)
    fingerprint = models.CharField(max_length=64)
    version = models.CharField(max_length=80)
    ciphertext = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["attachment", "fingerprint", "version"],
                name="chat_media_analysis_once",
            )
        ]


class ChatModerationCase(TimeStampedModel):
    report = models.OneToOneField(
        "admin_api.UserReport", on_delete=models.PROTECT, related_name="chat_case"
    )
    conversation = models.ForeignKey("chat.Conversation", on_delete=models.PROTECT)
    subject = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    batch = models.ForeignKey(ChatModerationBatch, on_delete=models.PROTECT)
    dedupe_key = models.CharField(max_length=64, unique=True)
    state = models.CharField(max_length=24, default="warning", db_index=True)
    notification = models.ForeignKey(
        "notifications.Notification", null=True, on_delete=models.SET_NULL
    )
    push_claimed_at = models.DateTimeField(null=True)
    evidence_ciphertext = models.TextField()
    policy_version = models.CharField(max_length=40)
    revision = models.PositiveIntegerField(default=1)
    resolved_at = models.DateTimeField(null=True)


class ChatPolicyNotice(TimeStampedModel):
    conversation = models.ForeignKey("chat.Conversation", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    case = models.ForeignKey(ChatModerationCase, null=True, on_delete=models.PROTECT)
    kind = models.CharField(max_length=20, default="warning")
    dedupe_key = models.CharField(max_length=100, unique=True)
    acknowledged_at = models.DateTimeField(null=True)
    acknowledged_sequence = models.PositiveBigIntegerField(null=True)


class AccountRestriction(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rental_restrictions",
    )
    case = models.OneToOneField(
        ChatModerationCase, on_delete=models.PROTECT, related_name="restriction"
    )
    state = models.CharField(max_length=20, default="pending_review", db_index=True)
    released_at = models.DateTimeField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "state"], name="chat_restriction_user_state")
        ]


class ChatModerationAppeal(TimeStampedModel):
    case = models.OneToOneField(
        ChatModerationCase, on_delete=models.PROTECT, related_name="appeal"
    )
    client_id = models.UUIDField()
    ciphertext = models.TextField()


class ChatModerationAction(TimeStampedModel):
    case = models.ForeignKey(
        ChatModerationCase, on_delete=models.PROTECT, related_name="actions"
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    client_id = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    action = models.CharField(max_length=24)
    notes = models.TextField()
    result_revision = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["case", "client_id"], name="chat_review_action_once"
            )
        ]


class GeminiUsageReservation(TimeStampedModel):
    """Conservative request admission across workers; never a billing guarantee."""

    day = models.DateField()
    requests = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["day"], name="chat_gemini_daily_admission")
        ]
