from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core_apps.common.models import TimeStampedModel


class DeviceToken(TimeStampedModel):
    class DeviceType(models.TextChoices):
        IOS = "ios", _("iOS")
        ANDROID = "android", _("Android")
        WEB = "web", _("Web")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="device_tokens",
        verbose_name=_("User"),
    )
    token = models.CharField(_("FCM Token"), max_length=512, unique=True)
    device_type = models.CharField(
        _("Device Type"),
        max_length=20,
        choices=DeviceType.choices,
        default=DeviceType.ANDROID,
    )
    device_name = models.CharField(
        _("Device Name"), max_length=100, blank=True, default=""
    )
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        verbose_name = _("Device Token")
        verbose_name_plural = _("Device Tokens")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["token"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.device_type} ({self.token[:12]}...)"
