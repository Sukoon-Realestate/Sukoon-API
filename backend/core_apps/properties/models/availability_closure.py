from django.db import models
from core_apps.common.models import TimeStampedModel


class AvailabilityClosure(TimeStampedModel):
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='dated_closures')
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    timezone = models.CharField(max_length=64, default='Africa/Cairo')
    revision = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)
    retained_visits = models.JSONField(default=list)

    class Meta:
        constraints = [models.CheckConstraint(check=models.Q(ends_at__gt=models.F('starts_at')),
            name='availability_closure_positive_range')]
