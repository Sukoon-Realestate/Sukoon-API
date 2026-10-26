"""Durable jobs can be safely resumed by Celery or the recovery command."""

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from ...transition_network_models import TransitionMatchRun
from ..planning import enabled_services
from .solver import calculate


@shared_task(name="features.process_transition_match")
def process_transition_match(identifier):
    with transaction.atomic():
        run = (
            TransitionMatchRun.objects.select_for_update()
            .select_related(
                "intent__user",
                "intent__lease__property__owner",
                "intent__lease__property__city",
                "intent__lease__property__property_type",
                "intent__source_transition",
            )
            .get(id=identifier)
        )
        if run.status != "queued":
            return run.status
        if "housing_transition_planning" not in enabled_services():
            return "paused"
        calculate(run)
        run.status = "result_ready"
        run.completed_at = timezone.now()
        run.revision += 1
        run.save()
        from ..advanced_planning_notifications import record

        record(run, None, "transition.result")
        for candidate in run.candidates.all():
            record(candidate, None, "transition.proposed")
        return run.status


def enqueue(identifier):
    try:
        process_transition_match.delay(identifier)
    except Exception:
        # Broker outage must not turn a committed job into a reported rejection.
        # The queued row remains visible and the recovery command dispatches it.
        return False
    return True
