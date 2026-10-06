from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core_apps.common.models import TimeStampedModel


class TicketMessage(TimeStampedModel):
    class SenderType(models.TextChoices):
        USER = "user", _("User")
        SUPPORT = "support", _("Support")

    ticket = models.ForeignKey(
        "support.Ticket",
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("Ticket"),
    )
    sender = models.CharField(
        _("Sender"),
        max_length=20,
        choices=SenderType.choices,
        default=SenderType.USER,
        db_index=True,
    )
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ticket_messages",
        verbose_name=_("Sender User"),
    )
    body = models.TextField(_("Message Body"))

    class Meta:
        verbose_name = _("Ticket Message")
        verbose_name_plural = _("Ticket Messages")
        ordering = ["created_at"]

    def __str__(self):
        return f"Message on {self.ticket.reference} by {self.sender}"
