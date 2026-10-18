from django.db import models
from django.urls import reverse
from core_apps.support.storage import SupportPrivateStorage
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
    file = models.FileField(_("File"), upload_to="support/attachments/", blank=True)
    private_file = models.FileField(upload_to="attachments/", blank=True, storage=SupportPrivateStorage())

    class Meta:
        verbose_name = _("Ticket Attachment")
        verbose_name_plural = _("Ticket Attachments")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.name} on Message {self.message_id}"

    @property
    def file_url(self) -> str:
        return reverse("support-attachment", kwargs={"id": self.id}) if self.private_file or self.file else ""
