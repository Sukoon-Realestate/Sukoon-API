from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from core_apps.virtual_tours import tasks
from core_apps.virtual_tours.models import TourRevision
from core_apps.virtual_tours.validation import validate_authoring
from .test_tours import synthetic_draft


def test_polling_dispatch_leaves_job_in_durable_outbox(settings):
    settings.VIRTUAL_TOUR_PROCESSOR_MODE = "polling"
    with patch.object(tasks.process_tour, "delay") as broker:
        tasks.dispatch_revision("revision", "hash")
    broker.assert_not_called()


def test_worker_requires_explicit_mode(settings):
    settings.VIRTUAL_TOUR_PROCESSOR_MODE = "celery"
    with pytest.raises(CommandError):
        call_command("run_virtual_tour_worker", once=True)


@pytest.mark.django_db(transaction=True)
def test_polling_worker_builds_queued_panorama_once_and_recovers_interruption(
    settings, property_obj
):
    settings.VIRTUAL_TOUR_PROCESSOR_MODE = "polling"
    _, revision, _ = synthetic_draft(property_obj)
    revision.source_hash, _ = validate_authoring(revision, revision.authoring)
    revision.processing_state = "processing"
    revision.save()
    TourRevision.objects.filter(pk=revision.pk).update(
        updated_at=timezone.now() - timedelta(minutes=21)
    )
    call_command("run_virtual_tour_worker", once=True)
    revision.refresh_from_db()
    assert revision.processing_state == "ready", revision.report
    assert revision.variants.count() == 1
    variant_id = revision.variants.get().id
    call_command("run_virtual_tour_worker", once=True)
    assert revision.variants.get().id == variant_id
