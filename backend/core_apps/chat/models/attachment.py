from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class ChatAttachment(TimeStampedModel):
    conversation = models.ForeignKey("chat.Conversation", on_delete=models.CASCADE)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    membership_period = models.UUIDField()
    client_upload_id = models.UUIDField()
    kind = models.CharField(max_length=16)
    state = models.CharField(max_length=16, default="ready")
    fingerprint = models.CharField(max_length=64)
    storage_key = models.CharField(max_length=200)
    thumbnail_key = models.CharField(max_length=200, blank=True)
    mime_type = models.CharField(max_length=64)
    byte_size = models.PositiveIntegerField()
    width = models.PositiveIntegerField(null=True)
    height = models.PositiveIntegerField(null=True)
    duration_ms = models.PositiveIntegerField(null=True)
    message = models.ForeignKey(
        "chat.Message",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="attachments",
    )
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "pkid"]
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "uploader", "client_upload_id"],
                name="unique_chat_upload_identity",
            )
        ]
