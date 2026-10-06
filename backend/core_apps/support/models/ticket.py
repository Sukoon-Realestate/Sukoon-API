from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core_apps.common.models import TimeStampedModel


class Ticket(TimeStampedModel):
    class Workspace(models.TextChoices):
        TENANT = "tenant", _("Tenant")
        OWNER = "owner", _("Owner")

    class Category(models.TextChoices):
        VISIT = "visit", _("Visit")
        PAYMENT = "payment", _("Payment")
        VERIFICATION = "verification", _("Verification")
        PROPERTY = "property", _("Property")
        REPORT_OWNER = "report_owner", _("Report Owner")
        REPORT_TENANT = "report_tenant", _("Report Tenant")
        OTHER = "other", _("Other")

    class Status(models.TextChoices):
        OPEN = "open", _("Open")
        IN_PROGRESS = "in_progress", _("In Progress")
        RESOLVED = "resolved", _("Resolved")
        CLOSED = "closed", _("Closed")

    reference = models.CharField(
        _("Reference"),
        max_length=30,
        unique=True,
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets",
        verbose_name=_("User"),
    )
    workspace = models.CharField(
        _("Workspace"),
        max_length=20,
        choices=Workspace.choices,
        default=Workspace.TENANT,
        db_index=True,
    )
    category = models.CharField(
        _("Category"),
        max_length=30,
        choices=Category.choices,
        default=Category.OTHER,
        db_index=True,
    )
    subject = models.CharField(_("Subject"), max_length=160)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )

    class Meta:
        verbose_name = _("Support Ticket")
        verbose_name_plural = _("Support Tickets")
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return f"{self.reference} - {self.subject} ({self.get_status_display()})"
