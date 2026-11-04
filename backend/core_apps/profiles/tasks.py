from celery import shared_task


@shared_task
def record_identity_expiry_reminders():
    from .identity_expiry import record_reminders
    return record_reminders()
