from django.conf import settings
from django.db import models


class ConversationWorkspace(models.Model):
    """Private display classification; never grants conversation access."""

    conversation = models.ForeignKey(
        "chat.Conversation", on_delete=models.CASCADE, related_name="workspace_contexts"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    workspace = models.CharField(
        max_length=16, choices=[(v, v) for v in ("individual", "owner", "student")]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user", "workspace"],
                name="chat_unique_viewer_workspace",
            )
        ]
