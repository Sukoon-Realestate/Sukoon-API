from celery import shared_task
from django.http import Http404
from django.db import transaction
from django.utils import timezone
from ...advanced_tender_models import TenderPackageRun
from ..planning import enabled_services
from .construction import calculate
from .access import get_tender


@shared_task(name="features.process_tender_packages")
def process_tender_packages(identifier):
    with transaction.atomic():
        run = (
            TenderPackageRun.objects.select_for_update(of=("self",))
            .select_related(
                "tender__active_snapshot",
                "tender__group",
                "tender__request",
                "snapshot",
                "created_by",
            )
            .get(id=identifier)
        )
        if run.status != "queued":
            return run.status
        if "collective_tender_planning" not in enabled_services():
            return "paused"
        from rest_framework.exceptions import APIException

        try:
            run.tender = get_tender(run.created_by, run.tender.id, lock=True)
        except (APIException, Http404):
            run.status = "source_changed"
            run.result = {"optimality_proven": False, "feasible_count": 0}
        else:
            calculate(run)
        run.completed_at = timezone.now()
        run.revision += 1
        run.save()
        from ..advanced_planning_notifications import record

        record(run, None, "tender.result")
        return run.status


def enqueue(identifier):
    try:
        process_tender_packages.delay(identifier)
    except Exception:
        return False  # Durable queued row is visible and can be safely re-enqueued.
    return True
