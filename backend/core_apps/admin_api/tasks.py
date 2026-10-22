from celery import shared_task


@shared_task
def dispatch_campaigns():
    from .services.push_campaigns import dispatch
    return dispatch()
