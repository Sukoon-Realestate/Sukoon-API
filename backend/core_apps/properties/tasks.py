from datetime import timedelta
from celery import shared_task
from django.utils import timezone


@shared_task
def purge_saved_search_reads():
    """Expire read receipts without deleting the successful-read watermark."""
    from .models import SavedSearchRead

    count, _ = SavedSearchRead.objects.filter(
        expires_at__lt=timezone.now() - timedelta(days=30)
    ).delete()
    return count
