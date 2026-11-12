from datetime import timedelta
from celery import shared_task
from django.utils import timezone


@shared_task
def purge_saved_search_reads():
    """Expire read receipts without deleting the successful-read watermark."""
    from django.db.models import Exists, OuterRef
    from .models import SavedSearchRead, SavedSearchReadItem, SavedSearchVisit

    cutoff = timezone.now() - timedelta(days=30)
    watermark = SavedSearchVisit.objects.filter(acknowledged_read_id=OuterRef("pk"), last_read_at__gte=cutoff)
    expired = (
        SavedSearchRead.objects.filter(expires_at__lt=cutoff)
        .annotate(active_watermark=Exists(watermark))
        .filter(active_watermark=False)
    )
    targets = list(expired.order_by("expires_at", "pk").values_list("pk", flat=True)[:100])
    items = list(
        SavedSearchReadItem.objects.filter(read_id__in=targets)
        .order_by("read_id", "property_identity")
        .values_list("pk", flat=True)[:500]
    )
    if items:
        SavedSearchReadItem.objects.filter(pk__in=items).delete()
    remaining = SavedSearchReadItem.objects.filter(read_id=OuterRef("pk"))
    completed = expired.filter(pk__in=targets).annotate(has_items=Exists(remaining)).filter(has_items=False)
    count = completed.count()
    completed.delete()
    return count
