from django.db import models
from django.utils.translation import gettext_lazy as _
from core_apps.common.models import TimeStampedModel


class PropertyType(TimeStampedModel):
    name = models.CharField(_("Name"), max_length=50, unique=True)
    slug = models.SlugField(_("Slug"), max_length=50, unique=True, help_text=_("Used in API queries, e.g. ?property_type=apartment"))
    description = models.TextField(_("Description"), blank=True, default="")

    class Meta:
        verbose_name = _("Property Type")
        verbose_name_plural = _("Property Types")
        ordering = ["name"]

    def __str__(self):
        return self.name
