from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core_apps.common.models import TimeStampedModel


class Notification(TimeStampedModel):
    class NotificationType(models.TextChoices):
        VISIT_REQUEST = "visit_request", _("Visit Request")
        VISIT_ACCEPTED = "visit_accepted", _("Visit Accepted")
        VISIT_REJECTED = "visit_rejected", _("Visit Rejected")
        NEW_MESSAGE = "new_message", _("New Message")
        PROPERTY_UPDATE = "property_update", _("Property Update")
        PROPERTY_VERIFIED = "property_verified", _("Property Verified")
        PROPERTY_VIEWS = "property_views", _("Property Views")
        DAILY_BUMP = "daily_bump", _("Daily Bump")
        NEW_PROPERTY = "new_property", _("New Property In Area")
        SECURITY_ALERT = "security_alert", _("Security Alert")
        ACCOUNT_VERIFICATION = "account_verification", _("Account Verification")
        VISIT_REVIEW = "visit_review", _("Visit Review")
        PROMOTION = "promotion", _("Promotion")
        GENERAL = "general", _("General Notification")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("User"),
    )
    notification_type = models.CharField(
        _("Notification Type"),
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
    )
    title = models.CharField(_("Title"), max_length=255)
    body = models.TextField(_("Body"), blank=True, default="")
    category = models.CharField(_("Category"), max_length=100, blank=True, default="")
    icon_type = models.CharField(
        _("Icon Type"), max_length=50, blank=True, default="bell"
    )
    is_read = models.BooleanField(_("Is Read"), default=False)
    read_at = models.DateTimeField(_("Read At"), null=True, blank=True)
    data = models.JSONField(_("Data Payload"), default=dict, blank=True)

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} -> {self.user.email}"
