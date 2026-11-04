from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedModel


class ViewingTimeProposal(TimeStampedModel):
    visit = models.ForeignKey('PropertyVisit', on_delete=models.CASCADE, related_name='time_proposals')
    proposer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    visit_revision = models.PositiveIntegerField()
    availability_revision = models.CharField(max_length=64)
    choices = models.JSONField(default=list)
    expires_at = models.DateTimeField()
    state = models.CharField(max_length=16, default='open')
    revision = models.PositiveIntegerField(default=1)
    selected_slot = models.CharField(max_length=36, blank=True)
