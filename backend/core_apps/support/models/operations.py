from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class TicketTransition(TimeStampedModel):
    ticket = models.ForeignKey(
        "support.Ticket", on_delete=models.PROTECT, related_name="transitions"
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    action = models.CharField(max_length=30)
    reason = models.CharField(max_length=1000)
    previous_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="support_transfers_from",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="support_transfers_to",
    )


class TicketInternalNote(TimeStampedModel):
    ticket = models.ForeignKey(
        "support.Ticket", on_delete=models.PROTECT, related_name="internal_notes"
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    body = models.TextField()
