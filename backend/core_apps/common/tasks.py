"""Non-business worker connectivity evidence."""

from celery import shared_task
from django.db import connection, transaction


@shared_task
def background_probe():
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL TRANSACTION READ ONLY")
            cursor.execute("SELECT 1")
            if cursor.fetchone() != (1,):
                raise RuntimeError("Database connectivity probe failed")
    return {"database_read": 1, "business_writes": 0}


@shared_task
def monitor_runtime():
    from .runtime_metrics import snapshot, evaluate_incidents
    return {"open_incidents": evaluate_incidents(snapshot())}


@shared_task
def maintain_chat():
    """Same maintenance as the existing worker, including its private-AI gates."""
    from core_apps.chat.moderation.queue import process_one
    from core_apps.chat.moderation.notifications import deliver_pending
    from core_apps.chat.services.group_outbox import drain_outbox, deliver_pushes

    process_one()
    deliver_pending()
    drain_outbox(limit=20)
    deliver_pushes(limit=20)
    return {"maintenance_cycles": 1}


@shared_task
def purge_chat_policy():
    from core_apps.chat.management.commands.run_chat_policy_worker import purge

    purge()
    return {"retention_cycles": 1}
