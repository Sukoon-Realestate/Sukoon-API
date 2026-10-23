from django.db import models


class ChatSearchDocument(models.Model):
    """Derived text only. Message visibility remains the source of authority."""

    message = models.OneToOneField(
        "chat.Message",
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="search_document",
    )
    body = models.TextField(default="", blank=True)
    links = models.JSONField(default=list, blank=True)
    revision = models.PositiveIntegerField(default=1)
