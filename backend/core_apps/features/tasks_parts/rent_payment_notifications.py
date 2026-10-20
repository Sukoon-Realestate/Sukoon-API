"""Rent reminders do not depend on commute/search/provider business jobs."""

from celery import shared_task


@shared_task(
    name="core_apps.features.tasks.process_rent_payment_notifications",
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
)
def process_rent_payment_notifications():
    from ..services.rent_payment_reminders import record_reminders, EVENT_KINDS
    from ..services.planning_notifications import deliver_planning_events

    result = record_reminders()
    result["dispatched"] = deliver_planning_events(event_kinds=EVENT_KINDS)
    return result
