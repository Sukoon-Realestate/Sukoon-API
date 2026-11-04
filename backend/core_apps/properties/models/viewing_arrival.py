from django.db import models
from core_apps.common.models import TimeStampedModel


class ViewingArrival(TimeStampedModel):
    visit = models.OneToOneField('PropertyVisit', on_delete=models.CASCADE, related_name='arrival_card')
    revision = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)
    meeting_point = models.CharField(max_length=300, blank=True)
    entrance = models.CharField(max_length=300, blank=True)
    instructions = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
