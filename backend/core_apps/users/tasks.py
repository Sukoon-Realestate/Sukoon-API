from celery import shared_task


@shared_task(name="core_apps.users.tasks.deliver_security_notices")
def deliver_security_notices():
    from .services.security_notices import deliver

    from .services.closure_delivery import deliver as deliver_closure, erase_files

    return {"security": deliver(), "closure": deliver_closure(), "erased_files": erase_files()}
