from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class MessageStar(TimeStampedModel):
    message = models.ForeignKey("chat.Message", on_delete=models.CASCADE, related_name="stars")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    membership_period = models.UUIDField()
    enabled = models.BooleanField(default=True)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["message", "user", "membership_period"], name="chat_unique_star_period")
        ]


class MessagePin(TimeStampedModel):
    message = models.OneToOneField("chat.Message", on_delete=models.CASCADE, related_name="pin")
    pinned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    expires_at = models.DateTimeField()


class MessageReadReceipt(TimeStampedModel):
    message = models.ForeignKey("chat.Message", on_delete=models.CASCADE, related_name="read_receipts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    membership_period = models.UUIDField()
    read_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["message", "user", "membership_period"], name="chat_unique_read_period")
        ]


class ChatQuickReply(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=60)
    content = models.CharField(max_length=2000)
    revision = models.PositiveIntegerField(default=1)
    deleted_at = models.DateTimeField(null=True, blank=True)


class MessagePoll(TimeStampedModel):
    message = models.OneToOneField("chat.Message", on_delete=models.CASCADE, related_name="poll")
    question = models.CharField(max_length=200)
    options = models.JSONField(default=list)
    allow_multiple = models.BooleanField(default=False)
    revision = models.PositiveIntegerField(default=1)
    closed_at = models.DateTimeField(null=True, blank=True)


class MessagePollVote(TimeStampedModel):
    poll = models.ForeignKey(MessagePoll, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    membership_period = models.UUIDField()
    option_ids = models.JSONField(default=list)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["poll", "user"], name="chat_unique_poll_voter")]


class ChatForwardBatch(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    operation_id = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    result = models.JSONField(default=dict)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "operation_id"], name="chat_unique_forward_batch")]
