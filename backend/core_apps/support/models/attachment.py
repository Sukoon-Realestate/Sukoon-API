from django.db import models
from django.utils.translation import gettext_lazy as _

from core_apps.common.models import TimeStampedModel


class TicketAttachment(TimeStampedModel):
    message = models.ForeignKey(
        "support.TicketMessage",
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("Message"),
    )
    name = models.CharField(_("File Name"), max_length=255)
    file = models.FileField(_("File"), upload_to="support/attachments/")

    class Meta:
        verbose_name = _("Ticket Attachment")
        verbose_name_plural = _("Ticket Attachments")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.name} on Message {self.message_id}"

    @property
    def file_url(self) -> str:
        if self.file and hasattr(self.file, "url"):
            return self.file.url
        return ""
