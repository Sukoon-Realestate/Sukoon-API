from celery import shared_task


@shared_task(acks_late=True)
def maintain_support_uploads():
    from core_apps.support.services.staged_attachments import scan_pending

    return scan_pending()
