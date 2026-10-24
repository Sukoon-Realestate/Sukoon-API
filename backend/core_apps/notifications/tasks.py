from celery import shared_task

@shared_task(name='core_apps.notifications.tasks.deliver_push')
def deliver_push():
    from .services.push_delivery import dispatch
    return dispatch()
