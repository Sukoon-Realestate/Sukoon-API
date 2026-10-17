"""Scheduled recovery and minimization for advanced housing workflows."""

from io import StringIO
from celery import shared_task


@shared_task(name="advanced_housing.recover_jobs")
def recover_jobs():
    from django.core.management import call_command

    call_command("process_advanced_housing_jobs", limit=50, stdout=StringIO())


@shared_task(name="advanced_housing.purge_private_inputs")
def purge_private_inputs():
    from .living_lab.retention import purge_due

    return purge_due(batch_size=200)
