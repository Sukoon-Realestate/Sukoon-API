from django.db import models
from .models import TimeStampedModel


class RuntimeIncident(TimeStampedModel):
    code = models.CharField(max_length=80, unique=True)
    state = models.CharField(max_length=20, default="open")
    occurrences = models.PositiveIntegerField(default=1)
    opened_at = models.DateTimeField(null=True)
    last_seen_at = models.DateTimeField(null=True)
    resolved_at = models.DateTimeField(null=True)
