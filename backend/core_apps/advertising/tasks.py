from celery import shared_task


@shared_task
def expire_advertisements():
    from core_apps.features.services.commerce_expiration import expire

    return expire(kinds=("advertising",))
