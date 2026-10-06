from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core_apps.common.models import TimeStampedModel


class UserReport(TimeStampedModel):
    class ReasonType(models.TextChoices):
        SPAM = "spam", _("Spam")
        FRAUD = "fraud", _("Fraud / Scam")
        ABUSIVE = "abusive", _("Abusive Language")
        MISLEADING = "misleading", _("Misleading Info")
        OTHER = "other", _("Other")

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        SUSPENDED = "suspended", _("Suspended")
        BANNED = "banned", _("Banned")
        DISMISSED = "dismissed", _("Dismissed")

    class AutomationLevel(models.TextChoices):
        HIGH = "high", _("High Risk")
        AUTO = "auto", _("Auto Detected")
        LOW = "low", _("Low Risk")

    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_received",
        verbose_name=_("Reported User"),
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_filed",
        verbose_name=_("Reporter"),
    )
    reason = models.CharField(_("Reason"), max_length=255)
    reason_type = models.CharField(
        _("Reason Type"),
        max_length=50,
        choices=ReasonType.choices,
        default=ReasonType.OTHER,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    automation_level = models.CharField(
        _("Automation Level"),
        max_length=20,
        choices=AutomationLevel.choices,
        default=AutomationLevel.AUTO,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_reports",
        verbose_name=_("Reviewed By"),
    )
    reviewed_at = models.DateTimeField(_("Reviewed At"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True, default="")

    class Meta:
        verbose_name = _("User Report")
        verbose_name_plural = _("User Reports")
        ordering = ["-created_at"]

    def __str__(self):
        reporter_name = self.reporter.email if self.reporter else "System / Automated"
        return f"Report against {self.reported_user.email} by {reporter_name}"
