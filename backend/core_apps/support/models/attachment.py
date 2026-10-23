from django.db import models
from django.conf import settings
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
        null=True,
        blank=True,
    )
    name = models.CharField(_("File Name"), max_length=255)
    file = models.FileField(_("File"), upload_to="support/attachments/", blank=True)
    private_file = models.FileField(
        upload_to="attachments/", blank=True, storage=SupportPrivateStorage()
    )

    # A rolling deployment may still have a writer from before digest binding.
    # NULL means no digest was recorded; it never represents verified bytes.
    content_sha256 = models.CharField(
        max_length=64, blank=True, null=True, editable=False
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.CASCADE,
        related_name="support_uploads",
    )
    pending_ticket = models.ForeignKey(
        "support.Ticket",
        null=True,
        on_delete=models.CASCADE,
        related_name="pending_uploads",
    )
    client_upload_id = models.UUIDField(null=True)
    creation_request_key = models.UUIDField(null=True)
    workspace = models.CharField(max_length=16, null=True)
    status = models.CharField(max_length=16, null=True)
    media_metadata = models.JSONField(null=True)
    private_content = models.BinaryField(null=True)
    expires_at = models.DateTimeField(null=True)
    scan_token = models.UUIDField(null=True)
    scan_until = models.DateTimeField(null=True)

    class Meta:
        verbose_name = _("Ticket Attachment")
        verbose_name_plural = _("Ticket Attachments")
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["uploader", "client_upload_id"], name="support_upload_identity"
            )
        ]

    def __str__(self):
        return f"{self.name} on Message {self.message_id}"

    @property
    def file_url(self) -> str:
        if not self.message_id or self.status not in {None, "attached"}:
            return ""
        return (
            reverse("support-attachment", kwargs={"id": self.id})
            if self.private_file or self.file
            else ""
        )
