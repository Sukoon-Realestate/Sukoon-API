"""Bounded scheduled delivery for explicitly requested statements only."""

from celery import shared_task
from ..services.rental_statement_delivery import generate_requested


@shared_task(acks_late=True)
def generate_requested_rental_statements():
    # A lost broker message or worker is recovered by the next scheduled scan.
    # The document's durable marker and locked queued status are the work queue.
    return generate_requested(limit=1)
