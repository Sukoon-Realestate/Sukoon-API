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
