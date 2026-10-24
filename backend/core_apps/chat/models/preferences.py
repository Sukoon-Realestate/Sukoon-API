"""Private conversation organization and account-wide communication consent."""

from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class ChatBlock(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_blocks")
    blocked_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_blocked_by")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "blocked_user"], name="unique_chat_block")]


class ChatList(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    workspace = models.CharField(max_length=16)
    organization = models.CharField(max_length=36, blank=True, default="")
    name = models.CharField(max_length=80)
    conversations = models.ManyToManyField("chat.Conversation", related_name="private_lists")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "workspace", "organization", "name"], name="unique_private_chat_list")]


class MessageEdit(TimeStampedModel):
    message = models.ForeignKey("chat.Message", on_delete=models.CASCADE, related_name="edits")
    revision = models.PositiveIntegerField()
    before = models.TextField()
    after = models.TextField()

    class Meta:
        ordering = ["revision"]
        constraints = [models.UniqueConstraint(fields=["message", "revision"], name="unique_chat_edit_revision")]
