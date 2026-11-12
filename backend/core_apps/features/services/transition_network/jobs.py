"""Durable jobs can be safely resumed by Celery or the recovery command."""

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from ...transition_network_models import TransitionMatchRun
from ..planning import enabled_services
from .solver import calculate, persist_options
from .commit import RELATED, locked_inputs, revalidate


@shared_task(name="features.process_transition_match")
def process_transition_match(identifier):
    run = TransitionMatchRun.objects.select_related(*("intent__" + value for value in RELATED)).get(id=identifier)
    if run.status != "queued":
        return run.status
    if "housing_transition_planning" not in enabled_services():
        return "paused"
    # Search and its provider-independent eligibility work hold no shared locks.
    # A crash leaves the durable queued row available for the recovery command.
    options = calculate(run)
    with transaction.atomic():
        current = locked_inputs(run, options)
        locked = TransitionMatchRun.objects.select_for_update(of=("self",)).get(pk=run.pk)
        if locked.status != "queued" or locked.revision != run.revision:
            return locked.status
        if "housing_transition_planning" not in enabled_services():
            return "paused"
        checked = revalidate(run, options, current)
        if checked is None:
            run.result_status, run.failure_code = "stale", "snapshot_stale"
            checked = []
        persist_options(run, checked)
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
