from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class PushCampaign(TimeStampedModel):
    protocol_version = models.PositiveSmallIntegerField(default=2)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    request_key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    title = models.CharField(max_length=180)
    body = models.TextField(max_length=2000)
    audience = models.CharField(max_length=20)
    state = models.CharField(max_length=24, default="preview")
    revision = models.PositiveIntegerField(default=1)
    preview_digest = models.CharField(max_length=64)
    confirmed_at = models.DateTimeField(null=True)
    cancelled_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["creator", "request_key"], name="campaign_original_request"
            )
        ]


class CampaignRecipient(TimeStampedModel):
    workspace = models.CharField(max_length=16, default="account")
    receipt_state = models.CharField(max_length=16, default="queued")
    campaign = models.ForeignKey(
        PushCampaign, on_delete=models.CASCADE, related_name="recipients"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    notification = models.OneToOneField(
        "notifications.Notification", on_delete=models.SET_NULL, null=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "user", "workspace"],
                name="campaign_one_workspace_receipt",
            )
        ]


class CampaignDelivery(TimeStampedModel):
    recipient = models.ForeignKey(
        CampaignRecipient, on_delete=models.CASCADE, related_name="deliveries"
    )
    device = models.ForeignKey(
        "notifications.DeviceToken", on_delete=models.SET_NULL, null=True
    )
    registration_digest = models.CharField(max_length=64)
    state = models.CharField(max_length=30, default="queued")
    attempt_token = models.UUIDField(null=True)
    attempt_started_at = models.DateTimeField(null=True)
    provider_reference = models.CharField(max_length=200, blank=True)
    failure_code = models.CharField(max_length=60, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipient", "device"], name="campaign_one_device"
            )
        ]
