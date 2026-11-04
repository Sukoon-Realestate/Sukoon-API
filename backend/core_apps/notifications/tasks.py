from celery import shared_task

@shared_task(name='core_apps.notifications.tasks.deliver_push')
def deliver_push():
    from .services.push_delivery import dispatch
    return dispatch()


@shared_task(name='core_apps.notifications.tasks.build_daily_digests')
def build_daily_digests():
    from .services.delivery_policy import build_digests
    return build_digests()
