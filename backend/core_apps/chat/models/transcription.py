from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class VoiceTranscription(TimeStampedModel):
    attachment = models.OneToOneField("chat.ChatAttachment", on_delete=models.CASCADE)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fingerprint = models.CharField(max_length=64)
    model = models.CharField(max_length=80)
    state = models.CharField(max_length=20, default="queued", db_index=True)
    ciphertext = models.TextField(blank=True)
    error_code = models.CharField(max_length=40, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    lease_token = models.UUIDField(null=True)
    lease_until = models.DateTimeField(null=True)
