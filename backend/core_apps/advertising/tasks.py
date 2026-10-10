from celery import shared_task
from django.utils import timezone

from .models import Advertisement


@shared_task
def expire_advertisements():
    return Advertisement.objects.filter(
        status=Advertisement.Status.ACTIVE,
        ends_at__lte=timezone.now(),
    ).update(status=Advertisement.Status.EXPIRED, updated_at=timezone.now())
