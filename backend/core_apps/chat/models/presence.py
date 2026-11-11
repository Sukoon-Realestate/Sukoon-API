from django.conf import settings
from django.db import models


class ChatPresenceLease(models.Model):
    """An expiring socket lease, independent of other tabs and worker processes."""

    connection_id = models.CharField(max_length=255, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, to_field="id", on_delete=models.CASCADE)
    expires_at = models.DateTimeField(db_index=True)
