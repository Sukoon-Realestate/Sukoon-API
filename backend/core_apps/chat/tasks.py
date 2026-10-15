from celery import shared_task


@shared_task(ignore_result=True)
def drain_chat_outbox():
    from .services.group_outbox import drain_outbox, deliver_pushes

    count = drain_outbox()
    deliver_pushes()
    return count


@shared_task(ignore_result=True)
def clean_chat_media():
    from .services.group_media_storage import cleanup_orphans

    return cleanup_orphans()
