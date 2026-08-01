from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from core_apps.common.models import TimeStampedModel

User = get_user_model()


class PropertyVisit(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = ("pending", _("Pending"))
        CONFIRMED = ("confirmed", _("Confirmed"))
        CANCELED = ("canceled", _("Canceled"))
        REJECTED = ("rejected", _("Rejected"))

    property = models.ForeignKey(
        "Property",
        on_delete=models.CASCADE,
        related_name="visits",
        verbose_name=_("Property"),
    )
    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="visits",
        verbose_name=_("Tenant"),
    )
    visit_date = models.DateField(_("Visit Date"))
    visit_time = models.TimeField(_("Visit Time"))
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    note = models.TextField(_("Note"), blank=True, default="")

    class Meta:
        verbose_name = _("Property Visit")
        verbose_name_plural = _("Property Visits")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "property", "visit_date", "visit_time"],
                name="unique_tenant_property_visit_slot",
            )
        ]

    def __str__(self):
        return f"Visit for {self.property.title} by {self.tenant.email} on {self.visit_date} at {self.visit_time}"
